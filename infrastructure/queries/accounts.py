"""
infrastructure/queries/accounts.py — Read-side queries for Accounts mode.

Implements AccountsQueryPort.
Queries directly against movements + movement_line_items.
No ORM — pure SQLAlchemy Core.
"""

from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import AccountsSummary, ClientStillOut, StillOutEntry
from domain.language import MovementDirection
from domain.ports import AccountsQueryPort
from infrastructure.db.tables import (
    clients_table,
    items_table,
    movement_line_items_table,
    movements_table,
)


class SqlAlchemyAccountsQuery(AccountsQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_still_out_for(
        self,
        workspace_id: str,
        client_id: str,
        item_id: str,
    ) -> Decimal:
        """
        SUM(SEND qty) - SUM(COLLECT qty) for one client + item.
        Returns Decimal("0") if no movements exist.
        """
        sent = await self._sum_direction(
            workspace_id, client_id, item_id, MovementDirection.SEND
        )
        collected = await self._sum_direction(
            workspace_id, client_id, item_id, MovementDirection.COLLECT
        )
        return sent - collected

    async def get_accounts_summary(self, workspace_id: str) -> AccountsSummary:
        """
        Return all clients with at least one non-zero Still Out entry.
        Each client row contains per-item breakdown.
        """
        # Load all clients in this workspace
        clients_result = await self.session.execute(
            sa.select(clients_table)
            .where(clients_table.c.workspace_id == workspace_id)
            .order_by(clients_table.c.name)
        )
        client_rows = clients_result.fetchall()

        # Load all items in this workspace (for label + unit lookup)
        items_result = await self.session.execute(
            sa.select(items_table).where(items_table.c.workspace_id == workspace_id)
        )
        items_by_id = {row.id: row for row in items_result.fetchall()}

        # Aggregate: SUM quantities per (client_id, item_id, direction)
        agg_result = await self.session.execute(
            sa.select(
                movements_table.c.client_id,
                movement_line_items_table.c.item_id,
                movements_table.c.direction,
                sa.func.sum(movement_line_items_table.c.quantity).label("total"),
            )
            .join(
                movement_line_items_table,
                movement_line_items_table.c.movement_id == movements_table.c.id,
            )
            .where(
                movements_table.c.workspace_id == workspace_id,
                movements_table.c.direction.in_(
                    [
                        MovementDirection.SEND,
                        MovementDirection.COLLECT,
                    ]
                ),
            )
            .group_by(
                movements_table.c.client_id,
                movement_line_items_table.c.item_id,
                movements_table.c.direction,
            )
        )

        # Build nested dict: client_id -> item_id -> {SEND: x, COLLECT: y}
        ledger: dict[str, dict[str, dict[str, Decimal]]] = {}
        for row in agg_result.fetchall():
            ledger.setdefault(row.client_id, {}).setdefault(
                row.item_id,
                {
                    MovementDirection.SEND: Decimal("0"),
                    MovementDirection.COLLECT: Decimal("0"),
                },
            )[row.direction] = Decimal(str(row.total))

        # Build result
        result_clients: list[ClientStillOut] = []
        for client_row in client_rows:
            client_ledger = ledger.get(client_row.id, {})
            entries: list[StillOutEntry] = []

            for item_id, direction_totals in client_ledger.items():
                still_out = direction_totals.get(
                    MovementDirection.SEND, Decimal("0")
                ) - direction_totals.get(MovementDirection.COLLECT, Decimal("0"))
                if still_out <= Decimal("0"):
                    continue
                item = items_by_id.get(item_id)
                if item is None:
                    continue
                entries.append(
                    StillOutEntry(
                        item_id=item_id,
                        item_label=item.label,
                        unit=item.unit,
                        quantity=still_out,
                    )
                )

            if entries:
                result_clients.append(
                    ClientStillOut(
                        client_id=client_row.id,
                        client_name=client_row.name,
                        entries=entries,
                    )
                )

        return AccountsSummary(clients=result_clients)

    # ── Private ───────────────────────────────────────────────────────────────

    async def _sum_direction(
        self,
        workspace_id: str,
        client_id: str,
        item_id: str,
        direction: MovementDirection,
    ) -> Decimal:
        result = await self.session.execute(
            sa.select(
                sa.func.coalesce(
                    sa.func.sum(movement_line_items_table.c.quantity),
                    0,
                ).label("total")
            )
            .join(
                movements_table,
                movements_table.c.id == movement_line_items_table.c.movement_id,
            )
            .where(
                movements_table.c.workspace_id == workspace_id,
                movements_table.c.client_id == client_id,
                movements_table.c.direction == direction,
                movement_line_items_table.c.item_id == item_id,
            )
        )
        row = result.first()
        return Decimal(str(row.total)) if row else Decimal("0")
