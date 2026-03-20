import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_create_item_group_returns_201(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(db_session)

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/item-groups",
        json={"name": "Beverages"},
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["workspace_id"] == workspace.id
    assert data["name"] == "Beverages"  # ItemGroup.create() strips + lowercases? verify
    assert "id" in data


@pytest.mark.anyio
async def test_create_item_group_accounts_workspace(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from domain.language import WorkspaceMode

    workspace, _, _ = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.ACCOUNTS
    )

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/item-groups",
        json={"name": "Containers"},
    )

    assert resp.status_code == 201


@pytest.mark.anyio
async def test_create_item_group_inventory_workspace(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from domain.language import WorkspaceMode

    workspace, _, _ = await seed_workspace_graph(
        db_session, mode=WorkspaceMode.INVENTORY
    )

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/item-groups",
        json={"name": "Frozen"},
    )

    assert resp.status_code == 201
