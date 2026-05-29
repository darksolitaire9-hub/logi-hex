# infrastructure/repositories/item_groups.py

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import ItemGroup
from domain.ports import ItemGroupRepositoryPort
from infrastructure.db.tables import item_groups_table


class SqlAlchemyItemGroupRepository(ItemGroupRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, group: ItemGroup) -> None:
        existing = await self.get_by_id(group.workspace_id, group.id)
        if existing is None:
            await self.session.execute(
                item_groups_table.insert().values(
                    id=group.id,
                    workspace_id=group.workspace_id,
                    name=group.name,
                )
            )
        else:
            await self.session.execute(
                sa.update(item_groups_table)
                .where(
                    (item_groups_table.c.id == group.id)
                    & (item_groups_table.c.workspace_id == group.workspace_id)
                )
                .values(name=group.name)
            )

    async def get_by_id(self, workspace_id: str, group_id: str) -> ItemGroup | None:
        result = await self.session.execute(
            sa.select(item_groups_table).where(
                (item_groups_table.c.id == group_id)
                & (item_groups_table.c.workspace_id == workspace_id)
            )
        )
        row = result.first()
        if row is None:
            return None
        return ItemGroup(
            id=row.id,
            workspace_id=row.workspace_id,
            name=row.name,
        )

    async def list_all(self, workspace_id: str) -> list[ItemGroup]:
        result = await self.session.execute(
            sa.select(item_groups_table)
            .where(item_groups_table.c.workspace_id == workspace_id)
            .order_by(item_groups_table.c.name)  # ← was created_at, doesn't exist
        )
        rows = result.fetchall()
        return [
            ItemGroup(
                id=row.id,
                workspace_id=row.workspace_id,
                name=row.name,
            )
            for row in rows
        ]

    async def delete(self, workspace_id: str, group_id: str) -> None:
        await self.session.execute(
            sa.delete(item_groups_table).where(
                (item_groups_table.c.id == group_id)
                & (item_groups_table.c.workspace_id == workspace_id)
            )
        )
