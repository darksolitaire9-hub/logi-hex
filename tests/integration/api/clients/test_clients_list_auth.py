import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_list_clients_requires_auth(
    unauth_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(db_session)

    response = await unauth_client.get(f"/api/workspaces/{workspace.id}/clients")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_list_clients_unknown_workspace_returns_404(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/api/workspaces/does-not-exist/clients")

    assert response.status_code == 404
