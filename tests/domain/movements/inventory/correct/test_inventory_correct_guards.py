from decimal import Decimal

import pytest

from domain.exceptions import (
    ArchivedItemError,
    CorrectionReasonRequiredError,
    EmptyMovementError,
    ItemNotFoundError,
    WorkspaceModeMismatchError,
)
from domain.language import CorrectionReason, WorkspaceMode
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
async def test_correct_without_reason_raises_for_opening_balance():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(CorrectionReasonRequiredError):
        await correct_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            actual_quantity=Decimal("3"),
            reason=CorrectionReason._OPENING_BALANCE,
            notes=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_correct_without_reason_raises_for_none():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(CorrectionReasonRequiredError):
        await correct_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            actual_quantity=Decimal("3"),
            reason=None,  # type: ignore[arg-type]
            notes=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_correct_negative_actual_quantity_raises():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(EmptyMovementError):
        await correct_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            actual_quantity=Decimal("-1"),
            reason=CorrectionReason.SHRINKAGE,
            notes=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_correct_in_accounts_mode_raises():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(WorkspaceModeMismatchError):
        await correct_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            item_id=ITEM_ID,
            actual_quantity=Decimal("3"),
            reason=CorrectionReason.SHRINKAGE,
            notes=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_correct_unknown_item_raises():
    item = make_item()
    other_id = "other-item"
    assert other_id != ITEM_ID

    stock_query = FakeStockQuery(stock={other_id: Decimal("5")})

    with pytest.raises(ItemNotFoundError):
        await correct_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=other_id,
            actual_quantity=Decimal("3"),
            reason=CorrectionReason.SHRINKAGE,
            notes=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_correct_rejects_archived_item():
    item = make_item(is_active=False)
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(ArchivedItemError):
        await correct_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            actual_quantity=Decimal("3"),
            reason=CorrectionReason.SHRINKAGE,
            notes=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )
