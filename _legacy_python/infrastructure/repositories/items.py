"""
infrastructure/repositories/items.py
Replaces infrastructure/repositories/tracking.py
"""

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Item, ItemGroup, Tag
from domain.ports import (
    ItemGroupRepositoryPort,
    ItemRepositoryPort,
    TagRepositoryPort,
)
from infrastructure.db.tables import (
    item_groups_table,
    item_tags_table,
    items_table,
    tags_table,
)

# ── Item Group ────────────────────────────────────────────────────────────────


class SqlAlchemyItemGroupRepository(ItemGroupRepositoryPort):
    def __init__(self, session: AsyncSession):
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
                    item_groups_table.c.id == group.id,
                    item_groups_table.c.workspace_id == group.workspace_id,
                )
                .values(name=group.name)
            )

    async def get_by_id(self, workspace_id: str, group_id: str) -> ItemGroup | None:
        result = await self.session.execute(
            sa.select(item_groups_table).where(
                item_groups_table.c.id == group_id,
                item_groups_table.c.workspace_id == workspace_id,
            )
        )
        row = result.first()
        if row is None:
            return None
        return _row_to_group(row)

    async def list_all(self, workspace_id: str) -> list[ItemGroup]:
        result = await self.session.execute(
            sa.select(item_groups_table)
            .where(item_groups_table.c.workspace_id == workspace_id)
            .order_by(item_groups_table.c.name)
        )
        return [_row_to_group(row) for row in result.fetchall()]

    async def delete(self, workspace_id: str, group_id: str) -> None:
        await self.session.execute(
            sa.delete(item_groups_table).where(
                item_groups_table.c.id == group_id,
                item_groups_table.c.workspace_id == workspace_id,
            )
        )


# ── Item ──────────────────────────────────────────────────────────────────────


class SqlAlchemyItemRepository(ItemRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, item: Item) -> None:
        existing = await self.get_by_id(item.workspace_id, item.id)
        if existing is None:
            await self.session.execute(
                items_table.insert().values(
                    id=item.id,
                    workspace_id=item.workspace_id,
                    group_id=item.group_id,
                    label=item.label,
                    unit=item.unit,
                    is_active=item.is_active,
                )
            )
        else:
            await self.session.execute(
                sa.update(items_table)
                .where(
                    items_table.c.id == item.id,
                    items_table.c.workspace_id == item.workspace_id,
                )
                .values(
                    label=item.label,
                    unit=item.unit,
                    group_id=item.group_id,
                    is_active=item.is_active,
                )
            )

    async def get_by_id(self, workspace_id: str, item_id: str) -> Item | None:
        result = await self.session.execute(
            sa.select(items_table).where(
                items_table.c.id == item_id,
                items_table.c.workspace_id == workspace_id,
            )
        )
        row = result.first()
        if row is None:
            return None
        return _row_to_item(row)

    async def list_all(self, workspace_id: str) -> list[Item]:
        result = await self.session.execute(
            sa.select(items_table)
            .where(items_table.c.workspace_id == workspace_id)
            .order_by(items_table.c.label)
        )
        return [_row_to_item(row) for row in result.fetchall()]

    async def list_active(self, workspace_id: str) -> list[Item]:
        result = await self.session.execute(
            sa.select(items_table)
            .where(
                items_table.c.workspace_id == workspace_id,
                items_table.c.is_active == sa.true(),
            )
            .order_by(items_table.c.label)
        )
        return [_row_to_item(row) for row in result.fetchall()]


# ── Tag ───────────────────────────────────────────────────────────────────────


class SqlAlchemyTagRepository(TagRepositoryPort):
    def __init__(self, session: AsyncSession):
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
                )
            )
        else:
            await self.session.execute(
                sa.update(tags_table)
                .where(
                    tags_table.c.id == tag.id,
                    tags_table.c.workspace_id == tag.workspace_id,
                )
                .values(name=tag.name, colour=tag.colour)
            )

    async def get_by_id(self, workspace_id: str, tag_id: str) -> Tag | None:
        result = await self.session.execute(
            sa.select(tags_table).where(
                tags_table.c.id == tag_id,
                tags_table.c.workspace_id == workspace_id,
            )
        )
        row = result.first()
        if row is None:
            return None
        return _row_to_tag(row)

    async def list_all(self, workspace_id: str) -> list[Tag]:
        result = await self.session.execute(
            sa.select(tags_table)
            .where(tags_table.c.workspace_id == workspace_id)
            .order_by(tags_table.c.name)
        )
        return [_row_to_tag(row) for row in result.fetchall()]

    async def assign_to_item(self, item_id: str, tag_id: str) -> None:
        # Ignore if already assigned
        existing = await self.session.execute(
            sa.select(item_tags_table).where(
                item_tags_table.c.item_id == item_id,
                item_tags_table.c.tag_id == tag_id,
            )
        )
        if existing.first() is None:
            await self.session.execute(
                item_tags_table.insert().values(
                    item_id=item_id,
                    tag_id=tag_id,
                )
            )

    async def remove_from_item(self, item_id: str, tag_id: str) -> None:
        await self.session.execute(
            sa.delete(item_tags_table).where(
                item_tags_table.c.item_id == item_id,
                item_tags_table.c.tag_id == tag_id,
            )
        )

    async def get_ids_for_item(self, item_id: str) -> list[str]:
        result = await self.session.execute(
            sa.select(item_tags_table.c.tag_id).where(
                item_tags_table.c.item_id == item_id,
            )
        )
        return [row.tag_id for row in result.fetchall()]


# ── Row mappers ───────────────────────────────────────────────────────────────


def _row_to_group(row: sa.Row) -> ItemGroup:
    return ItemGroup(
        id=row.id,
        workspace_id=row.workspace_id,
        name=row.name,
    )


def _row_to_item(row: sa.Row) -> Item:
    return Item(
        id=row.id,
        workspace_id=row.workspace_id,
        group_id=row.group_id,
        label=row.label,
        unit=row.unit,
        is_active=row.is_active,
    )


def _row_to_tag(row: sa.Row) -> Tag:
    return Tag(
        id=row.id,
        workspace_id=row.workspace_id,
        name=row.name,
        colour=row.colour,
    )
