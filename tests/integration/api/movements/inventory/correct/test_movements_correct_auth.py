import pytest

from domain.language import WorkspaceMode
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_unknown_workspace_returns_404(api_client, db_session):
    response = await api_client.post(
        "/api/workspaces/doesnotexist/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": "any",
            "actual_quantity": "5",
            "reason": "COUNT_CORRECTION",
        },
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_no_auth_header_returns_401(unauth_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await unauth_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        json={
            "item_id": item.id,
            "actual_quantity": "5",
            "reason": "COUNT_CORRECTION",
        },
    )

    assert response.status_code == 401