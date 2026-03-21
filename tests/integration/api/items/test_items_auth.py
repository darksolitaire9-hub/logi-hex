import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_create_item_requires_auth(
    unauth_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, item = await seed_workspace_graph(db_session)

    resp = await unauth_client.post(
        f"/api/workspaces/{workspace.id}/items",
        json={"group_id": item.group_id, "label": "Coke", "unit": "pcs"},
    )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_create_item_unknown_workspace_returns_404(
    api_client: AsyncClient,
) -> None:
    resp = await api_client.post(
        "/api/workspaces/does-not-exist/items",
        json={"group_id": "any", "label": "Coke", "unit": "pcs"},
    )

    assert resp.status_code == 404


@pytest.mark.anyio
async def test_create_item_missing_fields_returns_422(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(db_session)

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/items",
        json={"label": "Coke"},  # missing group_id and unit
    )

    assert resp.status_code == 422
