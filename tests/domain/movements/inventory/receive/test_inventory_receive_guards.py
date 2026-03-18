from decimal import Decimal

import pytest

from domain.exceptions import (
    ArchivedItemError,
    EmptyMovementError,
    ItemNotFoundError,
    WorkspaceModeMismatchError,
)
from domain.language import WorkspaceMode
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


@pytest.mark.asyncio
async def test_receive_negative_raises():
    item = make_item()

    with pytest.raises(EmptyMovementError):
        await receive_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("-1"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_receive_in_accounts_mode_raises():
    item = make_item()

    with pytest.raises(WorkspaceModeMismatchError):
        await receive_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            item_id=ITEM_ID,
            quantity=Decimal("5"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_receive_archived_item_raises():
    item = make_item(is_active=False)

    with pytest.raises(ArchivedItemError):
        await receive_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=ITEM_ID,
            quantity=Decimal("5"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_receive_unknown_item_raises():
    # repo has no matching item_id
    item = make_item()
    other_id = "other-item"
    assert other_id != ITEM_ID

    with pytest.raises(ItemNotFoundError):
        await receive_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            item_id=other_id,
            quantity=Decimal("5"),
            notes=None,
            tag_ids=None,
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )
