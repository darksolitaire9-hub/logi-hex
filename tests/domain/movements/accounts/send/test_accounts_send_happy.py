from decimal import Decimal

import pytest

from domain.language import MovementDirection, WorkspaceMode
from domain.services import send_items
from tests.domain.conftest import (
    CLIENT_ID,
    ITEM_ID,
    WS_ID,
    FakeClientRepository,
    FakeItemRepository,
    FakeMovementRepository,
    FakeUoW,
    make_client,
    make_item,
)


@pytest.mark.asyncio
async def test_send_creates_movement():
    client = make_client()
    item = make_item()
    movement_repo = FakeMovementRepository()
    uow = FakeUoW()

    result = await send_items(
        workspace_id=WS_ID,
        mode=WorkspaceMode.ACCOUNTS,
        client_id=CLIENT_ID,
        item_quantities={ITEM_ID: Decimal("3")},
        notes=None,
        tag_ids=None,
        client_repo=FakeClientRepository(client),
        item_repo=FakeItemRepository([item]),
        movement_repo=movement_repo,
        uow=uow,
    )

    assert result.direction == MovementDirection.SEND
    assert len(result.line_items) == 1
    assert result.line_items[0].quantity == Decimal("3")
    assert result.client_id == CLIENT_ID
    assert uow.committed is True
    assert len(movement_repo.saved) == 1
