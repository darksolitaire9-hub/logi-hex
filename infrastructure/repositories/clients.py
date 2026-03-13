from typing import List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Client
from domain.ports import ClientRepositoryPort
from infrastructure.db.tables import clients_table


class SqlAlchemyClientRepository(ClientRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_by_name(self, name: str) -> Client:
        normalized = name.lower().strip()
        result = await self.session.execute(
            sa.select(clients_table).where(clients_table.c.name == normalized)
        )
        row = result.first()
        if row is not None:
            return Client(id=row.id, name=row.name)

        client = Client.from_name(name)
        await self.session.execute(
            clients_table.insert().values(id=client.id, name=client.name)
        )
        return client

    async def list_all(self) -> List[Client]:
        result = await self.session.execute(sa.select(clients_table))
        rows = result.fetchall()
        return [Client(id=row.id, name=row.name) for row in rows]
