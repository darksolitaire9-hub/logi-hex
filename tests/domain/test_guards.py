"""
Tests for cross-cutting guards: mode mismatch, archived item.
"""

from decimal import Decimal

import pytest

from domain.exceptions import ArchivedItemError, WorkspaceModeMismatchError
from domain.language import WorkspaceMode
from domain.services import receive_stock, send_items
from tests.domain.conftest import (
    CLIENT_ID,
    ITEM_ID,
    WS_ID,
    FakeAccountsQuery,
    FakeClientRepository,
    FakeItemRepository,
    FakeMovementRepository,
    FakeUoW,
    make_client,
    make_item,
)


@pytest.mark.asyncio
async def test_send_in_inventory_mode_raises():
    """Send is Accounts-only — must be rejected in Inventory mode."""
    client = make_client()
    item = make_item()

    with pytest.raises(WorkspaceModeMismatchError):
        await send_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,  # wrong mode
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("2")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_receive_in_accounts_mode_raises():
    """Receive is Inventory-only — must be rejected in Accounts mode."""
    item = make_item()

    with pytest.raises(WorkspaceModeMismatchError):
        await receive_stock(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,  # wrong mode
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

    with pytest.raises(ArchivedItemError) as exc_info:
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

    assert "Steel Box" in str(exc_info.value)
