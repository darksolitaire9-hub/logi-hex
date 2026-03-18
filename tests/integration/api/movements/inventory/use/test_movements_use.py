from decimal import Decimal

import pytest

from domain.language import WorkspaceMode
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_use_movement_happy_path(api_client, db_session):
    # Seed inventory workspace and starting stock via RECEIVE
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    # First receive some stock so use is allowed
    receive_response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/receive",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "quantity": "10",
            "tag_ids": [],
        },
    )
    assert receive_response.status_code == 201, receive_response.text

    # Then use part of it
    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/use",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "quantity": "4",
            "notes": "Kitchen use",
            "tag_ids": [],
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["workspace_id"] == workspace.id
    assert data["direction"] == "USE"
    assert data["mode"] == "INVENTORY"
    assert data["client_id"] is None
    assert data["client_name"] is None
    assert data["correction_reason"] is None
    assert data["notes"] == "Kitchen use"
    assert data["occurred_at"] is not None
    assert data["created_at"] is not None
    assert data["tags"] == []

    li = data["line_items"][0]
    assert li["item_id"] == item.id
    assert li["item_label"] == "Steel Box"
    assert li["unit"] == "pcs"
    assert Decimal(str(li["quantity"])) == Decimal("4")
