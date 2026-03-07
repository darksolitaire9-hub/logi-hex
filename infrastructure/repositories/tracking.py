# infrastructure/repositories/tracking.py
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import TrackingCategory, TrackingItem
from domain.ports import (
    TrackingCategoryRepositoryPort,
    TrackingItemRepositoryPort,
)
from infrastructure.db.tables import (
    tracking_categories_table,
    tracking_items_table,
)


class SqlAlchemyTrackingCategoryRepository(TrackingCategoryRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[TrackingCategory]:
        result = await self.session.execute(sa.select(tracking_categories_table))
        rows = result.fetchall()
        return [
            TrackingCategory(
                id=row.id,
                name=row.name,
                enforce_returns=row.enforce_returns,
            )
            for row in rows
        ]

    async def get_by_id(self, category_id: str) -> Optional[TrackingCategory]:
        result = await self.session.execute(
            sa.select(tracking_categories_table).where(
                tracking_categories_table.c.id == category_id
            )
        )
        row = result.first()
        if row is None:
            return None
        return TrackingCategory(
            id=row.id,
            name=row.name,
            enforce_returns=row.enforce_returns,
        )

    async def save(self, category: TrackingCategory) -> None:
        existing = await self.get_by_id(category.id)
        if existing is None:
            await self.session.execute(
                tracking_categories_table.insert().values(
                    id=category.id,
                    name=category.name,
                    enforce_returns=category.enforce_returns,
                )
            )
        else:
            await self.session.execute(
                sa.update(tracking_categories_table)
                .where(tracking_categories_table.c.id == category.id)
                .values(
                    name=category.name,
                    enforce_returns=category.enforce_returns,
                )
            )

    async def delete(self, category_id: str) -> None:
        await self.session.execute(
            sa.delete(tracking_categories_table).where(
                tracking_categories_table.c.id == category_id
            )
        )


class SqlAlchemyTrackingItemRepository(TrackingItemRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all_by_category(self, category_id: str) -> List[TrackingItem]:
        result = await self.session.execute(
            sa.select(tracking_items_table).where(
                tracking_items_table.c.category_id == category_id
            )
        )
        rows = result.fetchall()
        return [
            TrackingItem(
                id=row.id,
                category_id=row.category_id,
                label=row.label,
            )
            for row in rows
        ]

    async def get_by_id(self, item_id: str) -> Optional[TrackingItem]:
        result = await self.session.execute(
            sa.select(tracking_items_table).where(tracking_items_table.c.id == item_id)
        )
        row = result.first()
        if row is None:
            return None
        return TrackingItem(
            id=row.id,
            category_id=row.category_id,
            label=row.label,
        )

    async def save(self, item: TrackingItem) -> None:
        existing = await self.get_by_id(item.id)
        if existing is None:
            await self.session.execute(
                tracking_items_table.insert().values(
                    id=item.id,
                    category_id=item.category_id,
                    label=item.label,
                )
            )
        else:
            await self.session.execute(
                sa.update(tracking_items_table)
                .where(tracking_items_table.c.id == item.id)
                .values(
                    category_id=item.category_id,
                    label=item.label,
                )
            )

    async def delete(self, item_id: str) -> None:
        await self.session.execute(
            sa.delete(tracking_items_table).where(tracking_items_table.c.id == item_id)
        )
