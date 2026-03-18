from decimal import Decimal

import pytest

from domain.language import WorkspaceMode
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_correct_movement_happy_path(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "actual_quantity": "7",
            "reason": "COUNT_CORRECTION",
            "notes": "Weekly count",
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert data["workspace_id"] == workspace.id
    assert data["direction"] == "CORRECT"
    assert data["mode"] == "INVENTORY"
    assert data["client_id"] is None
    assert data["client_name"] is None
    assert data["correction_reason"] == "COUNT_CORRECTION"
    assert data["notes"] == "Weekly count"
    assert data["occurred_at"] is not None
    assert data["created_at"] is not None
    assert data["tags"] == []

    li = data["line_items"][0]
    assert li["item_id"] == item.id
    assert li["item_label"] == "Steel Box"
    assert li["unit"] == "pcs"
    assert Decimal(str(li["quantity"])) is not None


@pytest.mark.anyio
async def test_correct_movement_shrinkage_reason(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "actual_quantity": "0",
            "reason": "SHRINKAGE",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["correction_reason"] == "SHRINKAGE"


@pytest.mark.anyio
async def test_correct_movement_notes_optional(api_client, db_session):
    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/correct",
        headers={"Authorization": "Bearer test-token"},
        json={
            "item_id": item.id,
            "actual_quantity": "5",
            "reason": "COUNT_CORRECTION",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["notes"] is None