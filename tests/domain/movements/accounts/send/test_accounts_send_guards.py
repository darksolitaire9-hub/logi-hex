from decimal import Decimal

import pytest

from domain.exceptions import (
    ArchivedItemError,
    ClientNotFoundError,
    EmptyMovementError,
    WorkspaceModeMismatchError,
)
from domain.language import WorkspaceMode
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
async def test_send_in_inventory_mode_raises():
    client = make_client()
    item = make_item()

    with pytest.raises(WorkspaceModeMismatchError):
        await send_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
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
async def test_send_skips_zero_quantities_and_raises_empty():
    client = make_client()
    item = make_item()

    with pytest.raises(EmptyMovementError):
        await send_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("0")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_send_rejects_archived_item():
    client = make_client()
    item = make_item(is_active=False)

    with pytest.raises(ArchivedItemError):
        await send_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
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
async def test_send_unknown_client_raises():
    other_client = make_client()
    # Fake repo returns a client with a different id
    other_client.id = "other-client"

    with pytest.raises(ClientNotFoundError):
        await send_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("1")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(other_client),
            item_repo=FakeItemRepository([make_item()]),
            movement_repo=FakeMovementRepository(),
            uow=FakeUoW(),
        )
