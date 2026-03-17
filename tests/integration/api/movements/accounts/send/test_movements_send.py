# tests/integration/api/test_movements_send.py

from decimal import Decimal

import pytest

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_send_movement_happy_path(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "3"}],
            "notes": "Test send",
            "tag_ids": [],
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["workspace_id"] == workspace.id
    assert data["direction"] == "SEND"
    assert data["mode"] == "ACCOUNTS"
    assert data["client_id"] == client.id
    assert data["client_name"] == "alice"
    assert data["occurred_at"] is not None
    assert data["created_at"] is not None
    assert data["notes"] == "Test send"
    assert data["correction_reason"] is None

    li = data["line_items"][0]
    assert li["item_id"] == item.id
    assert li["item_label"] == "Steel Box"
    assert li["unit"] == "pcs"
    assert Decimal(str(li["quantity"])) == Decimal("3")
    assert data["tags"] == []


@pytest.mark.anyio
async def test_send_movement_notes_optional(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["notes"] is None


@pytest.mark.anyio
async def test_send_movement_duplicate_item_ids_aggregated(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [
                {"item_id": item.id, "quantity": "2"},
                {"item_id": item.id, "quantity": "3"},
            ],
            "tag_ids": [],
        },
    )

    assert response.status_code == 201, response.text
    assert Decimal(str(response.json()["line_items"][0]["quantity"])) == Decimal("5")
