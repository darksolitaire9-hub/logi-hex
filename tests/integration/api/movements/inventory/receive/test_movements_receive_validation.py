import pytest

from domain.language import WorkspaceMode
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_zero_quantity_returns_400(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/receive",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "quantity": "0",
            "tag_ids": [],
        },
    )

    assert response.status_code == 400
    assert "greater than zero" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_missing_item_id_returns_422(api_client, db_session):
    workspace, _, _ = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/receive",
        headers={"Authorization": "Bearer test-token"},
        json={
            "quantity": "5",
            "tag_ids": [],
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_missing_quantity_returns_422(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/receive",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "tag_ids": [],
        },
    )

    assert response.status_code == 422
