"""
infrastructure/repositories/clients.py
"""

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Client
from domain.ports import ClientRepositoryPort
from infrastructure.db.tables import clients_table


class SqlAlchemyClientRepository(ClientRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, client: Client) -> None:
        existing = await self.get_by_id(client.workspace_id, client.id)
        if existing is None:
            await self.session.execute(
                clients_table.insert().values(
                    id=client.id,
                    workspace_id=client.workspace_id,
                    name=client.name,
                )
            )
        # clients are immutable after creation — name is the identity

    async def get_by_id(self, workspace_id: str, client_id: str) -> Client | None:
        result = await self.session.execute(
            sa.select(clients_table).where(
                clients_table.c.id == client_id,
                clients_table.c.workspace_id == workspace_id,
            )
        )
        row = result.first()
        if row is None:
            return None
        return _row_to_client(row)

    async def get_by_name(self, workspace_id: str, name: str) -> Client | None:
        result = await self.session.execute(
            sa.select(clients_table).where(
                clients_table.c.workspace_id == workspace_id,
                clients_table.c.name == name.lower().strip(),
            )
        )
        row = result.first()
        if row is None:
            return None
        return _row_to_client(row)

    async def list_all(self, workspace_id: str) -> list[Client]:
        result = await self.session.execute(
            sa.select(clients_table)
            .where(clients_table.c.workspace_id == workspace_id)
            .order_by(clients_table.c.name)
        )
        return [_row_to_client(row) for row in result.fetchall()]


def _row_to_client(row: sa.Row) -> Client:
    return Client(
        id=row.id,
        workspace_id=row.workspace_id,
        name=row.name,
    )
