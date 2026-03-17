import pytest

from domain.language import WorkspaceMode
from infrastructure.db.tables import items_table
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_inventory_mode_workspace_returns_409_for_collect(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/collect",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_archived_item_returns_400_for_collect(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    # Seed SEND so StillOut > 0
    send_response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )
    assert send_response.status_code == 201, send_response.text

    await db_session.execute(
        items_table.update().where(items_table.c.id == item.id).values(is_active=False)
    )
    await db_session.commit()

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/collect",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_insufficient_still_out_returns_409(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    # SEND 2, then try to COLLECT 3
    send_response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "2"}],
            "tag_ids": [],
        },
    )
    assert send_response.status_code == 201, send_response.text

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/collect",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "3"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "only has" in detail
    assert "You cannot collect" in detail
    assert "Steel Box" in detail  # item_label from seed_workspace_graph


@pytest.mark.anyio
async def test_unknown_client_returns_404_for_collect(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    # Seed SEND for the real client so StillOut exists
    send_response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )
    assert send_response.status_code == 201, send_response.text

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/collect",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": "does-not-exist",
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 404
