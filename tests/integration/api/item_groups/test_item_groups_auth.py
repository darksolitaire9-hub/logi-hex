import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_create_item_group_requires_auth(
    unauth_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(db_session)

    resp = await unauth_client.post(
        f"/api/workspaces/{workspace.id}/item-groups",
        json={"name": "Beverages"},
    )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_create_item_group_unknown_workspace_returns_404(
    api_client: AsyncClient,
) -> None:
    resp = await api_client.post(
        "/api/workspaces/does-not-exist/item-groups",
        json={"name": "Beverages"},
    )

    assert resp.status_code == 404
