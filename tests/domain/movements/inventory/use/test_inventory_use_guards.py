from decimal import Decimal

import pytest

from domain.exceptions import (
    ArchivedItemError,
    EmptyMovementError,
    InsufficientStockError,
    ItemNotFoundError,
    WorkspaceModeMismatchError,
)
from domain.language import WorkspaceMode
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
async def test_use_exceeds_stock_raises():
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


@pytest.mark.asyncio
async def test_use_zero_quantity_raises():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(EmptyMovementError):
        await use_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("0"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_use_negative_quantity_raises():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(EmptyMovementError):
        await use_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("-1"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_use_in_accounts_mode_raises():
    item = make_item()
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(WorkspaceModeMismatchError):
        await use_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            item_id=ITEM_ID,
            quantity=Decimal("1"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_use_unknown_item_raises():
    item = make_item()
    other_id = "other-item"
    assert other_id != ITEM_ID

    stock_query = FakeStockQuery(stock={other_id: Decimal("5")})

    with pytest.raises(ItemNotFoundError):
        await use_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=other_id,
            quantity=Decimal("1"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            stock_query=stock_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_use_rejects_archived_item():
    item = make_item(is_active=False)
    stock_query = FakeStockQuery(stock={ITEM_ID: Decimal("5")})

    with pytest.raises(ArchivedItemError):
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
