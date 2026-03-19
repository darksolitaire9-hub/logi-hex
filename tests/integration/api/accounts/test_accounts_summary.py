from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.api.conftest import seed_workspace_graph


@pytest.mark.anyio
async def test_accounts_summary_empty_workspace(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workspace, _, _ = await seed_workspace_graph(db_session)
    # No movements logged yet

    resp = await api_client.get(f"/api/workspaces/{workspace.id}/accounts")

    assert resp.status_code == 200
    data = resp.json()
    assert data["clients"] == []
    assert Decimal(str(data["grand_total"])) == Decimal("0")


@pytest.mark.anyio
async def test_accounts_summary_after_send_and_collect(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from domain.language import MovementDirection
    from infrastructure.db.tables import movement_line_items_table, movements_table

    workspace, client, item = await seed_workspace_graph(db_session)

    # Manually seed one SEND of 5 and one COLLECT of 2
    import uuid
    from datetime import datetime, timezone

    send_id = uuid.uuid4().hex
    collect_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc)

    await db_session.execute(
        movements_table.insert().values(
            id=send_id,
            workspace_id=workspace.id,
            client_id=client.id,
            direction=MovementDirection.SEND,
            timestamp=now,
        )
    )
    await db_session.execute(
        movement_line_items_table.insert().values(
            movement_id=send_id, item_id=item.id, quantity=5, label=item.label
        )
    )

    await db_session.execute(
        movements_table.insert().values(
            id=collect_id,
            workspace_id=workspace.id,
            client_id=client.id,
            direction=MovementDirection.COLLECT,
            timestamp=now,
        )
    )
    await db_session.execute(
        movement_line_items_table.insert().values(
            movement_id=collect_id,
            item_id=item.id,
            quantity=2,
            label=item.label,
        )
    )
    await db_session.commit()

    resp = await api_client.get(f"/api/workspaces/{workspace.id}/accounts")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["clients"]) == 1
    client_row = data["clients"][0]
    assert client_row["client_id"] == client.id
    assert client_row["client_name"] == client.name
    assert client_row["is_settled"] is False
    assert len(client_row["entries"]) == 1
    entry = client_row["entries"][0]
    assert entry["item_id"] == item.id
    assert entry["item_label"] == item.label
    assert entry["unit"] == item.unit
    assert Decimal(str(entry["quantity"])) == Decimal("3")
    assert Decimal(str(client_row["total"])) == Decimal("3")
    assert Decimal(str(data["grand_total"])) == Decimal("3")
