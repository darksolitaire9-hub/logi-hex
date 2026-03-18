from decimal import Decimal

import pytest

from domain.language import MovementDirection, WorkspaceMode
from domain.services import receive_stock
from tests.domain.conftest import (
    ITEM_ID,
    WS_ID,
    FakeItemRepository,
    FakeMovementRepository,
    FakeUoW,
    make_item,
)


@pytest.mark.asyncio
async def test_receive_creates_movement():
    item = make_item()
    movement_repo = FakeMovementRepository()
    uow = FakeUoW()

    result = await receive_stock(
        workspace_id=WS_ID,
        mode=WorkspaceMode.INVENTORY,
        item_id=ITEM_ID,
        quantity=Decimal("10"),
        notes=None,
        tag_ids=None,
        item_repo=FakeItemRepository([item]),
        movement_repo=movement_repo,
        uow=uow,
    )

    assert result.direction == MovementDirection.RECEIVE
    assert result.line_items[0].quantity == Decimal("10")
    assert uow.committed is True
    assert len(movement_repo.saved) == 1
