# tests/integration/api/test_movements_send_guards.py

import pytest

from domain.language import WorkspaceMode
from infrastructure.db.tables import items_table
from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_inventory_mode_workspace_returns_409(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_archived_item_returns_400(api_client, db_session):
    workspace, client, item = await seed_workspace_graph(db_session)

    await db_session.execute(
        items_table.update().where(items_table.c.id == item.id).values(is_active=False)
    )
    await db_session.commit()

    response = await api_client.post(
        f"/api/workspaces/{workspace.id}/movements/send",
        headers={"Authorization": "Bearer test-token"},
        json={
            "client_id": client.id,
            "items": [{"item_id": item.id, "quantity": "1"}],
            "tag_ids": [],
        },
    )

    assert response.status_code == 400
