import pytest

from domain.language import WorkspaceMode
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_missing_reason_returns_422(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "actual_quantity": "5",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_invalid_reason_returns_422(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "actual_quantity": "5",
            "reason": "NOT_A_VALID_REASON",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_missing_item_id_returns_422(api_client, db_session):
    workspace, _, _ = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "actual_quantity": "5",
            "reason": "COUNT_CORRECTION",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_missing_actual_quantity_returns_422(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "reason": "COUNT_CORRECTION",
        },
    )

    assert response.status_code == 422
