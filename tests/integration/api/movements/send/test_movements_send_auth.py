# tests/integration/api/test_movements_send_auth.py

import pytest

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_unknown_workspace_returns_404(api_client, db_session):
    response = await api_client.post(
        "/api/workspaces/doesnotexist/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": "any",
            "items": [{"item_id": "any", "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_no_auth_header_returns_401(unauth_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    response = await unauth_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 401
