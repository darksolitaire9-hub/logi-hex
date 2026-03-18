import pytest

from domain.language import WorkspaceMode
from infrastructure.db.tables import items_table
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_accounts_mode_workspace_returns_409(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.ACCOUNTS
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/use",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "quantity": "5",
            "tag_ids": [],
        },
    )

    assert response.status_code == 409
    assert "USE" in response.json()["detail"]
    assert "ACCOUNTS" in response.json()["detail"]


@pytest.mark.anyio
async def test_archived_item_returns_400(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    await db_session.execute(
        items_table.update().where(items_table.c.id == item.id).values(is_active=False)
    )
    await db_session.commit()

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/use",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "quantity": "5",
            "tag_ids": [],
        },
    )

    assert response.status_code == 400
    assert "archived" in response.json()["detail"].lower()
    assert "Steel Box" in response.json()["detail"]


@pytest.mark.anyio
async def test_unknown_item_returns_404(api_client, db_session):
    workspace, _, _ = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/use",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": "nonexistent-item-id",
            "quantity": "5",
            "tag_ids": [],
        },
    )

    assert response.status_code == 404
    assert "nonexistent-item-id" in response.json()["detail"]


@pytest.mark.anyio
async def test_insufficient_stock_returns_409(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    # No prior RECEIVE → stock is 0
    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/use",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "quantity": "1",
            "tag_ids": [],
        },
    )

    assert response.status_code == 409
    assert "stock" in response.json()["detail"].lower()
