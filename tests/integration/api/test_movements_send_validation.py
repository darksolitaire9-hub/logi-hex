# tests/integration/api/test_movements_send_validation.py

import pytest

from domain.language import WorkspaceMode
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_empty_items_list_returns_400(api_client, db_session):
    workspace, client, _ = await seed_workspace_graph(db_session)

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={"client_id": client.id, "items": [], "tag_ids": []},
    )

    assert response.status_code == 400
    assert "item" in response.json()["detail"].lower()


@pytest.mark.anyio
async def test_missing_client_id_returns_422(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(db_session)

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={"items": [{"item_id": item.id, "quantity": "1"}], "tag_ids": []},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_missing_items_field_returns_422(api_client, db_session):
    workspace, client, _ = await seed_workspace_graph(db_session)

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={"client_id": client.id},
    )

    assert response.status_code == 422
