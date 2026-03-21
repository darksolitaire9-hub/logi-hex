import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_create_item_unknown_group_returns_404(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(db_session)

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/items",
        json={"group_id": "does-not-exist", "label": "Coke", "unit": "pcs"},
    )

    assert resp.status_code == 404


@pytest.mark.anyio
async def test_create_item_opening_stock_in_accounts_workspace_returns_409(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from domain.language import WorkspaceMode

    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.ACCOUNTS
    )

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/items",
        json={
            "group_id": item.group_id,
            "label": "Box",
            "unit": "pcs",
            "opening_quantity": "5",
        },
    )

    assert resp.status_code == 409
