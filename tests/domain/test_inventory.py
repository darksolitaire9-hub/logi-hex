"""
Tests for Inventory mode movements: Receive, Use, Correct.
Focus: Use guard and Correct delta calculation are the critical paths.
"""

from decimal import Decimal

import pytest

from domain.exceptions import (
    ArchivedItemError,
    CorrectionReasonRequiredError,
    EmptyMovementError,
    InsufficientStockError,
)
from domain.language import CorrectionReason, MovementDirection, WorkspaceMode
from domain.services import correct_stock, receive_stock, use_stock
from tests.domain.conftest import (
    ITEM_ID,
    WS_ID,
    FakeItemRepository,
    FakeMovementRepository,
    FakeStockQuery,
    FakeUoW,
    make_item,
)

# ── Receive ───────────────────────────────────────────────────────────────────


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


@pytest.mark.asyncio
async def test_receive_zero_raises():
    item = make_item()

    with pytest.raises(EmptyMovementError):
        await receive_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("0"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )


# ── Use ───────────────────────────────────────────────────────────────────────


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
    """Using exactly what is in stock must succeed."""
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


@pytest.mark.asyncio
async def test_use_exceeds_stock_raises():
    """The Use guard: cannot use more than In Stock."""
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("3")})

    with pytest.raises(InsufficientStockError) as exc_info:
        await use_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("10"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )

    err = exc_info.value
    assert err.in_stock == Decimal("3")
    assert err.requested == Decimal("10")
    assert err.item_label == "Steel Box"


@pytest.mark.asyncio
async def test_use_empty_stock_raises_with_empty_message():
    """When stock is zero the error message says 'empty', not a number."""
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("0")})

    with pytest.raises(InsufficientStockError) as exc_info:
        await use_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("1"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )

    assert "empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_use_nothing_written_on_guard_failure():
    item = make_item()
    movement_repo = FakeMovementRepository()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("2")})

    with pytest.raises(InsufficientStockError):
        await use_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("99"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=movement_repo,
            stock_query=stock_query,
            uow=FakeUoW(),
        )

    assert len(movement_repo.saved) == 0


# ── Correct ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_correct_positive_delta():
    """Actual > current: delta is positive (found more stock)."""
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
    assert result.line_items[0].quantity == Decimal("3")  # delta = 8 - 5


@pytest.mark.asyncio
async def test_correct_negative_delta_shrinkage():
    """Actual < current: delta is negative (shrinkage)."""
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

    assert result.line_items[0].quantity == Decimal("-4")  # delta = 6 - 10
    assert result.correction_reason == CorrectionReason.SHRINKAGE


@pytest.mark.asyncio
async def test_correct_to_zero_is_valid():
    """Correcting actual to 0 must succeed — all stock gone."""
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

    assert result.line_items[0].quantity == Decimal("-5")  # delta = 0 - 5


@pytest.mark.asyncio
async def test_correct_without_reason_raises():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(CorrectionReasonRequiredError):
        await correct_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            actual_quantity=Decimal("3"),
            reason=CorrectionReason._OPENING_BALANCE,  # internal only
            notes=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )
