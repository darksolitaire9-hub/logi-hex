"""
infrastructure/repositories/movements.py
Replaces infrastructure/repositories/transactions.py
"""

from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Movement, MovementLineItem
from domain.language import CorrectionReason, MovementDirection
from domain.ports import MovementRepositoryPort
from infrastructure.db.tables import (
    movement_line_items_table,
    movement_tags_table,
    movements_table,
)


class SqlAlchemyMovementRepository(MovementRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, movement: Movement) -> None:
        """
        Persist movement header + all line items + tag associations.
        Called inside a Unit of Work — caller commits.
        """
        await self.session.execute(
            movements_table.insert().values(
                id=movement.id,
                workspace_id=movement.workspace_id,
                direction=movement.direction,
                timestamp=movement.timestamp,
                client_id=movement.client_id,
                client_name=movement.client_name,
                correction_reason=(
                    movement.correction_reason.value
                    if movement.correction_reason
                    else None
                ),
                notes=movement.notes,
            )
        )

        for li in movement.line_items:
            await self.session.execute(
                movement_line_items_table.insert().values(
                    movement_id=movement.id,
                    item_id=li.item_id,
                    label=li.label,
                    quantity=li.quantity,
                )
            )

        for tag_id in movement.tag_ids:
            await self.session.execute(
                movement_tags_table.insert().values(
                    movement_id=movement.id,
                    tag_id=tag_id,
                )
            )

    async def list_by_workspace(self, workspace_id: str) -> list[Movement]:
        result = await self.session.execute(
            sa.select(movements_table)
            .where(movements_table.c.workspace_id == workspace_id)
            .order_by(movements_table.c.timestamp.desc())
        )
        return [await self._hydrate(row) for row in result.fetchall()]

    async def list_by_client(self, workspace_id: str, client_id: str) -> list[Movement]:
        result = await self.session.execute(
            sa.select(movements_table)
            .where(
                movements_table.c.workspace_id == workspace_id,
                movements_table.c.client_id == client_id,
            )
            .order_by(movements_table.c.timestamp.desc())
        )
        return [await self._hydrate(row) for row in result.fetchall()]

    async def list_by_item(self, workspace_id: str, item_id: str) -> list[Movement]:
        """
        Return all movements that contain a given item in their line items.
        Uses a subquery on movement_line_items to find matching movement ids.
        """
        subq = (
            sa.select(movement_line_items_table.c.movement_id)
            .where(movement_line_items_table.c.item_id == item_id)
            .scalar_subquery()
        )
        result = await self.session.execute(
            sa.select(movements_table)
            .where(
                movements_table.c.workspace_id == workspace_id,
                movements_table.c.id.in_(subq),
            )
            .order_by(movements_table.c.timestamp.desc())
        )
        return [await self._hydrate(row) for row in result.fetchall()]

    # ── Private ───────────────────────────────────────────────────────────────

    async def _hydrate(self, row: sa.Row) -> Movement:
        """Reconstruct a full Movement from a header row + child rows."""
        line_items = await self._load_line_items(row.id)
        tag_ids = await self._load_tag_ids(row.id)

        return Movement(
            id=row.id,
            workspace_id=row.workspace_id,
            direction=MovementDirection(row.direction),
            timestamp=row.timestamp,
            line_items=line_items,
            client_id=row.client_id,
            client_name=row.client_name,
            correction_reason=(
                CorrectionReason(row.correction_reason)
                if row.correction_reason
                else None
            ),
            tag_ids=tag_ids,
            notes=row.notes,
        )

    async def _load_line_items(self, movement_id: str) -> list[MovementLineItem]:
        result = await self.session.execute(
            sa.select(movement_line_items_table).where(
                movement_line_items_table.c.movement_id == movement_id
            )
        )
        return [
            MovementLineItem(
                item_id=row.item_id,
                label=row.label,
                quantity=Decimal(str(row.quantity)),
            )
            for row in result.fetchall()
        ]

    async def _load_tag_ids(self, movement_id: str) -> list[str]:
        result = await self.session.execute(
            sa.select(movement_tags_table.c.tag_id).where(
                movement_tags_table.c.movement_id == movement_id
            )
        )
        return [row.tag_id for row in result.fetchall()]
