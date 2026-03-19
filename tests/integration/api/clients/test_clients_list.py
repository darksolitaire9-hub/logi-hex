import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_list_clients_returns_seeded_client(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, client, _ = await seed_workspace_graph(db_session)

    response = await api_client.get(f"/api/workspaces/{workspace.id}/clients")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    ids = [c["id"] for c in data]
    assert client.id in ids


@pytest.mark.anyio
async def test_list_clients_returns_empty_list_for_empty_workspace(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from domain.entities import Workspace
    from domain.language import WorkspaceMode
    from infrastructure.db.tables import workspaces_table

    workspace = Workspace.create(
        name="Empty Workspace",
        mode=WorkspaceMode.ACCOUNTS,
        owner_user_id="user-123",
    )
    await db_session.execute(
        workspaces_table.insert().values(
            id=workspace.id,
            name=workspace.name,
            mode=workspace.mode.value,
            owner_user_id=workspace.owner_user_id,
            created_at=workspace.created_at,
        )
    )
    await db_session.commit()

    response = await api_client.get(f"/api/workspaces/{workspace.id}/clients")

    assert response.status_code == 200
    assert response.json() == []
