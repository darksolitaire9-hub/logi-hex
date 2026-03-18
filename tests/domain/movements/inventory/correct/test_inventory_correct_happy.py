from decimal import Decimal

import pytest

from domain.language import CorrectionReason, MovementDirection, WorkspaceMode
from domain.services import correct_stock
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
async def test_correct_positive_delta():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    result = await correct_stock(
        workspace_id=WS_ID,
        mode=WorkspaceMode.INVENTORY,
        item_id=ITEM_ID,
        actual_quantity=Decimal("8"),
        reason=CorrectionReason.COUNT_CORRECTION,
        notes=None,
        item_repo=FakeItemRepository([item]),
        movement_repo=FakeMovementRepository(),
        stock_query=stock_query,
        uow=FakeUoW(),
    )

    assert result.direction == MovementDirection.CORRECT
    assert result.line_items[0].quantity == Decimal("3")


@pytest.mark.asyncio
async def test_correct_negative_delta_shrinkage():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("10")})

    result = await correct_stock(
        workspace_id=WS_ID,
        mode=WorkspaceMode.INVENTORY,
        item_id=ITEM_ID,
        actual_quantity=Decimal("6"),
        reason=CorrectionReason.SHRINKAGE,
        notes="Damaged in storage",
        item_repo=FakeItemRepository([item]),
        movement_repo=FakeMovementRepository(),
        stock_query=stock_query,
        uow=FakeUoW(),
    )

    assert result.line_items[0].quantity == Decimal("-4")
    assert result.correction_reason == CorrectionReason.SHRINKAGE


@pytest.mark.asyncio
async def test_correct_to_zero_is_valid():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    result = await correct_stock(
        workspace_id=WS_ID,
        mode=WorkspaceMode.INVENTORY,
        item_id=ITEM_ID,
        actual_quantity=Decimal("0"),
        reason=CorrectionReason.SHRINKAGE,
        notes=None,
        item_repo=FakeItemRepository([item]),
        movement_repo=FakeMovementRepository(),
        stock_query=stock_query,
        uow=FakeUoW(),
    )

    assert result.line_items[0].quantity == Decimal("-5")
