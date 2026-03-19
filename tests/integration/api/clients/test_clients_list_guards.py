import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from domain.language import WorkspaceMode
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_list_clients_inventory_workspace_returns_409(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.get(f"/api/workspaces/{workspace.id}/clients")

    assert response.status_code == 409
