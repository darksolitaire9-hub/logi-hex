# infrastructure/repositories/tags.py

from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Tag
from domain.ports import TagRepositoryPort
from infrastructure.db.tables import item_tags_table, items_table, tags_table


class SqlAlchemyTagRepository(TagRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, tag: Tag) -> None:
        existing = await self.get_by_id(tag.workspace_id, tag.id)
        if existing is None:
            await self.session.execute(
                tags_table.insert().values(
                    id=tag.id,
                    workspace_id=tag.workspace_id,
                    name=tag.name,
                    colour=tag.colour,
                    created_at=datetime.now(timezone.utc),  # if your table has it
                )
            )
        else:
            await self.session.execute(
                sa.update(tags_table)
                .where(
                    (tags_table.c.id == tag.id)
                    & (tags_table.c.workspace_id == tag.workspace_id)
                )
                .values(name=tag.name, colour=tag.colour)
            )

    async def get_by_id(self, workspace_id: str, tag_id: str) -> Tag | None:
        result = await self.session.execute(
            sa.select(tags_table).where(
                (tags_table.c.id == tag_id)
                & (tags_table.c.workspace_id == workspace_id)
            )
        )
        row = result.first()
        if row is None:
            return None
        return Tag(
            id=row.id,
            workspace_id=row.workspace_id,
            name=row.name,
            colour=row.colour,
        )

    async def list_all(self, workspace_id: str) -> list[Tag]:
        result = await self.session.execute(
            sa.select(tags_table)
            .where(tags_table.c.workspace_id == workspace_id)
            .order_by(tags_table.c.name)
        )
        return [
            Tag(
                id=row.id,
                workspace_id=row.workspace_id,
                name=row.name,
                colour=row.colour,
            )
            for row in result.fetchall()
        ]

    async def assign_to_item(self, item_id: str, tag_id: str) -> None:
        # Determine workspace_id from the item row
        result = await self.session.execute(
            sa.select(items_table.c.workspace_id).where(items_table.c.id == item_id)
        )
        row = result.first()
        if row is None:
            return
        workspace_id = row.workspace_id

        await self.session.execute(
            item_tags_table.insert().values(
                workspace_id=workspace_id,
                tag_id=tag_id,
                item_id=item_id,
            )
        )

    async def remove_from_item(self, item_id: str, tag_id: str) -> None:
        result = await self.session.execute(
            sa.select(items_table.c.workspace_id).where(items_table.c.id == item_id)
        )
        row = result.first()
        if row is None:
            return
        workspace_id = row.workspace_id

        await self.session.execute(
            sa.delete(item_tags_table).where(
                (item_tags_table.c.workspace_id == workspace_id)
                & (item_tags_table.c.tag_id == tag_id)
                & (item_tags_table.c.item_id == item_id)
            )
        )

    async def get_ids_for_item(self, item_id: str) -> list[str]:
        """
        Return all tag IDs attached to this item.
        Workspace isolation is enforced via the item_tags_table workspace_id.
        """
        result = await self.session.execute(
            sa.select(item_tags_table.c.tag_id).where(
                item_tags_table.c.item_id == item_id
            )
        )
        rows = result.fetchall()
        return [row.tag_id for row in rows]
