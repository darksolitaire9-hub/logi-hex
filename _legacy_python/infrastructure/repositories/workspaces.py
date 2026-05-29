"""
infrastructure/repositories/workspaces.py
"""

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Workspace
from domain.language import WorkspaceMode
from domain.ports import WorkspaceRepositoryPort
from infrastructure.db.tables import workspaces_table


class SqlAlchemyWorkspaceRepository(WorkspaceRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, workspace: Workspace) -> None:
        existing = await self.get_by_id(workspace.id)
        if existing is None:
            await self.session.execute(
                workspaces_table.insert().values(
                    id=workspace.id,
                    name=workspace.name,
                    mode=workspace.mode,
                    owner_user_id=workspace.owner_user_id,
                    created_at=workspace.created_at,
                )
            )
        else:
            await self.session.execute(
                sa.update(workspaces_table)
                .where(workspaces_table.c.id == workspace.id)
                .values(name=workspace.name)
                # mode and owner_user_id are immutable after creation
            )

    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        result = await self.session.execute(
            sa.select(workspaces_table).where(workspaces_table.c.id == workspace_id)
        )
        row = result.first()
        if row is None:
            return None
        return _row_to_workspace(row)

    async def list_by_owner(self, owner_user_id: str) -> list[Workspace]:
        result = await self.session.execute(
            sa.select(workspaces_table)
            .where(workspaces_table.c.owner_user_id == owner_user_id)
            .order_by(workspaces_table.c.created_at)
        )
        return [_row_to_workspace(row) for row in result.fetchall()]


def _row_to_workspace(row: sa.Row) -> Workspace:
    return Workspace(
        id=row.id,
        name=row.name,
        mode=WorkspaceMode(row.mode),
        owner_user_id=row.owner_user_id,
        created_at=row.created_at,
    )
