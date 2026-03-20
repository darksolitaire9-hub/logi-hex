import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_create_item_group_missing_name_returns_422(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(db_session)

    resp = await api_client.post(
        f"/api/workspaces/{workspace.id}/item-groups",
        json={},
    )

    assert resp.status_code == 422
