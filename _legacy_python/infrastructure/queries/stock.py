"""
infrastructure/queries/stock.py — Read-side queries for Inventory mode.

Implements StockQueryPort.
Stock formula: SUM(RECEIVE) - SUM(USE) + SUM(CORRECT deltas)
CORRECT line items store the delta directly (can be negative).
"""

from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import InventorySummary, ItemStock
from domain.language import CorrectionReason, MovementDirection, StockState
from domain.ports import StockQueryPort
from infrastructure.db.tables import (
    item_groups_table,
    item_tags_table,
    items_table,
    movement_line_items_table,
    movements_table,
)

# Directions that add to stock (positive contribution)
_POSITIVE = [MovementDirection.RECEIVE]
# Directions that subtract from stock (negative contribution)
_NEGATIVE = [MovementDirection.USE]
# Directions whose line item quantity is already a signed delta
_DELTA = [MovementDirection.CORRECT]


class SqlAlchemyStockQuery(StockQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stock_for(self, workspace_id: str, item_id: str) -> Decimal:
        received = await self._sum_directions(workspace_id, item_id, _POSITIVE)
        used = await self._sum_directions(workspace_id, item_id, _NEGATIVE)
        corrections = await self._sum_directions(workspace_id, item_id, _DELTA)
        return received - used + corrections

    async def get_inventory_summary(self, workspace_id: str) -> InventorySummary:
        # Load groups for label lookup
        groups_result = await self.session.execute(
            sa.select(item_groups_table).where(
                item_groups_table.c.workspace_id == workspace_id
            )
        )
        groups_by_id = {row.id: row for row in groups_result.fetchall()}

        # Load all items
        items_result = await self.session.execute(
            sa.select(items_table)
            .where(items_table.c.workspace_id == workspace_id)
            .order_by(items_table.c.label)
        )
        item_rows = items_result.fetchall()

        # Aggregate movements for all items in one query
        agg_result = await self.session.execute(
            sa.select(
                movement_line_items_table.c.item_id,
                movements_table.c.direction,
                sa.func.sum(movement_line_items_table.c.quantity).label("total"),
            )
            .join(
                movements_table,
                movements_table.c.id == movement_line_items_table.c.movement_id,
            )
            .where(
                movements_table.c.workspace_id == workspace_id,
                movements_table.c.direction.in_(_POSITIVE + _NEGATIVE + _DELTA),
                # Exclude _OPENING_BALANCE from CORRECT direction
                # so opening stock appears as normal Receive in stock math
                # (opening balance uses RECEIVE direction so already covered)
            )
            .group_by(
                movement_line_items_table.c.item_id,
                movements_table.c.direction,
            )
        )

        # Build: item_id -> direction -> total
        ledger: dict[str, dict[str, Decimal]] = {}
        for row in agg_result.fetchall():
            ledger.setdefault(row.item_id, {})[row.direction] = Decimal(str(row.total))

        # Check which items have any CORRECT movements (for has_corrections flag)
        corrections_result = await self.session.execute(
            sa.select(movement_line_items_table.c.item_id)
            .join(
                movements_table,
                movements_table.c.id == movement_line_items_table.c.movement_id,
            )
            .where(
                movements_table.c.workspace_id == workspace_id,
                movements_table.c.direction == MovementDirection.CORRECT,
                movements_table.c.correction_reason
                != CorrectionReason._OPENING_BALANCE,
            )
            .distinct()
        )
        items_with_corrections = {row.item_id for row in corrections_result.fetchall()}

        # Load tag associations for all items
        tags_result = await self.session.execute(
            sa.select(item_tags_table).where(
                item_tags_table.c.item_id.in_([r.id for r in item_rows])
            )
        )
        tags_by_item: dict[str, list[str]] = {}
        for row in tags_result.fetchall():
            tags_by_item.setdefault(row.item_id, []).append(row.tag_id)

        # Build result
        stock_items: list[ItemStock] = []
        for item_row in item_rows:
            item_ledger = ledger.get(item_row.id, {})
            received = item_ledger.get(MovementDirection.RECEIVE, Decimal("0"))
            used = item_ledger.get(MovementDirection.USE, Decimal("0"))
            corrections = item_ledger.get(MovementDirection.CORRECT, Decimal("0"))
            in_stock = received - used + corrections

            group = groups_by_id.get(item_row.group_id)
            group_name = group.name if group else ""

            stock_items.append(
                ItemStock(
                    item_id=item_row.id,
                    item_label=item_row.label,
                    unit=item_row.unit,
                    group_id=item_row.group_id,
                    group_name=group_name,
                    in_stock=in_stock,
                    tag_ids=tags_by_item.get(item_row.id, []),
                    has_corrections=item_row.id in items_with_corrections,
                )
            )

        return InventorySummary(items=stock_items)

    # ── Private ───────────────────────────────────────────────────────────────

    async def _sum_directions(
        self,
        workspace_id: str,
        item_id: str,
        directions: list[MovementDirection],
    ) -> Decimal:
        result = await self.session.execute(
            sa.select(
                sa.func.coalesce(
                    sa.func.sum(movement_line_items_table.c.quantity), 0
                ).label("total")
            )
            .join(
                movements_table,
                movements_table.c.id == movement_line_items_table.c.movement_id,
            )
            .where(
                movements_table.c.workspace_id == workspace_id,
                movement_line_items_table.c.item_id == item_id,
                movements_table.c.direction.in_(directions),
            )
        )
        row = result.first()
        return Decimal(str(row.total)) if row else Decimal("0")
