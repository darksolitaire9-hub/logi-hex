from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_create_item_returns_201(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, item = await seed_workspace_graph(db_session)
    group_id = item.group_id

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/items",
        json={"group_id": group_id, "label": "Coke", "unit": "pcs"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["workspace_id"] == workspace.id
    assert data["group_id"] == group_id
    assert data["label"] == "Coke"
    assert data["unit"] == "pcs"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.anyio
async def test_create_item_with_opening_stock_returns_201(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from domain.language import WorkspaceMode

    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/items",
        json={
            "group_id": item.group_id,
            "label": "Salmon",
            "unit": "kg",
            "opening_quantity": "10.5",
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["label"] == "Salmon"
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_create_item_zero_opening_stock_behaves_as_plain_create(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from domain.language import WorkspaceMode

    workspace, _, item = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/items",
        json={
            "group_id": item.group_id,
            "label": "Water",
            "unit": "L",
            "opening_quantity": "0",
        },
    )

    assert resp.status_code == 201
