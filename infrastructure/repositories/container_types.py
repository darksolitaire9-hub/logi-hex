# infrastructure/repositories/container_types.py
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import ContainerType
from domain.ports import ContainerTypeRepositoryPort
from infrastructure.db.tables import container_types_table


class SqlAlchemyContainerTypeRepository(ContainerTypeRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[ContainerType]:
        result = await self.session.execute(sa.select(container_types_table))
        rows = result.fetchall()
        return [ContainerType(id=row.id, label=row.label) for row in rows]

    async def get_by_id(self, type_id: str) -> Optional[ContainerType]:
        result = await self.session.execute(
            sa.select(container_types_table).where(
                container_types_table.c.id == type_id
            )
        )
        row = result.first()
        if row is None:
            return None
        return ContainerType(id=row.id, label=row.label)

    async def save(self, container_type: ContainerType) -> None:
        # Upsert by id
        existing = await self.get_by_id(container_type.id)
        if existing is None:
            await self.session.execute(
                container_types_table.insert().values(
                    id=container_type.id,
                    label=container_type.label,
                )
            )
        else:
            await self.session.execute(
                sa.update(container_types_table)
                .where(container_types_table.c.id == container_type.id)
                .values(label=container_type.label)
            )

    async def delete(self, type_id: str) -> None:
        await self.session.execute(
            sa.delete(container_types_table).where(
                container_types_table.c.id == type_id
            )
        )
