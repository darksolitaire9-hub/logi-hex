from decimal import Decimal

import pytest

from domain.language import MovementDirection, WorkspaceMode
from domain.services import use_stock
from tests.domain.conftest import (
    ITEM_ID,
    WS_ID,
    FakeItemRepository,
    FakeMovementRepository,
    FakeStockQuery,
    FakeUoW,
    make_item,
)


@pytest.mark.asyncio
async def test_use_within_stock_succeeds():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("10")})
    uow = FakeUoW()

    result = await use_stock(
        workspace_id=WS_ID,
        mode=WorkspaceMode.INVENTORY,
        item_id=ITEM_ID,
        quantity=Decimal("4"),
        notes=None,
        tag_ids=None,
        item_repo=FakeItemRepository([item]),
        movement_repo=FakeMovementRepository(),
        stock_query=stock_query,
        uow=uow,
    )

    assert result.direction == MovementDirection.USE
    assert result.line_items[0].quantity == Decimal("4")
    assert uow.committed is True


@pytest.mark.asyncio
async def test_use_exact_stock_succeeds():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    result = await use_stock(
        workspace_id=WS_ID,
        mode=WorkspaceMode.INVENTORY,
        item_id=ITEM_ID,
        quantity=Decimal("5"),
        notes=None,
        tag_ids=None,
        item_repo=FakeItemRepository([item]),
        movement_repo=FakeMovementRepository(),
        stock_query=stock_query,
        uow=FakeUoW(),
    )

    assert result.line_items[0].quantity == Decimal("5")
