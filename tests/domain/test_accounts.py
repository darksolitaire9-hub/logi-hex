"""
Tests for Accounts mode movements: Send and Collect.
Focus: Collect guard is the critical path.
"""

from decimal import Decimal

import pytest

from domain.exceptions import (
    ArchivedItemError,
    EmptyMovementError,
    InsufficientStillOutError,
    WorkspaceModeMismatchError,
)
from domain.language import MovementDirection, WorkspaceMode
from domain.services import collect_items, send_items
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

# ── Send ──────────────────────────────────────────────────────────────────────


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


@pytest.mark.asyncio
async def test_send_skips_zero_quantities():
    client = make_client()
    item = make_item()
    movement_repo = FakeMovementRepository()

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
            movement_repo=movement_repo,
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


# ── Collect ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_collect_within_still_out_succeeds():
    client = make_client()
    item = make_item()
    movement_repo = FakeMovementRepository()
    uow = FakeUoW()

    # Alice has 5 pcs still out
    accounts_query = FakeAccountsQuery(still_out={(CLIENT_ID, ITEM_ID): Decimal("5")})

    result = await collect_items(
        workspace_id=WS_ID,
        mode=WorkspaceMode.ACCOUNTS,
        client_id=CLIENT_ID,
        item_quantities={ITEM_ID: Decimal("3")},
        notes=None,
        tag_ids=None,
        client_repo=FakeClientRepository(client),
        item_repo=FakeItemRepository([item]),
        movement_repo=movement_repo,
        accounts_query=accounts_query,
        uow=uow,
    )

    assert result.direction == MovementDirection.COLLECT
    assert result.line_items[0].quantity == Decimal("3")
    assert uow.committed is True


@pytest.mark.asyncio
async def test_collect_exact_still_out_succeeds():
    """Collecting exactly what the client has out must succeed."""
    client = make_client()
    item = make_item()
    accounts_query = FakeAccountsQuery(still_out={(CLIENT_ID, ITEM_ID): Decimal("5")})

    result = await collect_items(
        workspace_id=WS_ID,
        mode=WorkspaceMode.ACCOUNTS,
        client_id=CLIENT_ID,
        item_quantities={ITEM_ID: Decimal("5")},
        notes=None,
        tag_ids=None,
        client_repo=FakeClientRepository(client),
        item_repo=FakeItemRepository([item]),
        movement_repo=FakeMovementRepository(),
        accounts_query=accounts_query,
        uow=FakeUoW(),
    )

    assert result.line_items[0].quantity == Decimal("5")


@pytest.mark.asyncio
async def test_collect_exceeds_still_out_raises():
    """The Collect guard: cannot collect more than Still Out."""
    client = make_client()
    item = make_item()
    accounts_query = FakeAccountsQuery(still_out={(CLIENT_ID, ITEM_ID): Decimal("3")})

    with pytest.raises(InsufficientStillOutError) as exc_info:
        await collect_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("5")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            accounts_query=accounts_query,
            uow=FakeUoW(),
        )

    err = exc_info.value
    assert err.still_out == Decimal("3")
    assert err.requested == Decimal("5")
    assert err.client_name == "alice"
    assert err.item_label == "Steel Box"


@pytest.mark.asyncio
async def test_collect_zero_still_out_raises():
    """Client has nothing out — any collect must be rejected."""
    client = make_client()
    item = make_item()
    accounts_query = FakeAccountsQuery(still_out={})  # nothing out

    with pytest.raises(InsufficientStillOutError):
        await collect_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("1")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            accounts_query=accounts_query,
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_collect_nothing_written_on_guard_failure():
    """If the guard fails, zero movements must be saved."""
    client = make_client()
    item = make_item()
    movement_repo = FakeMovementRepository()
    accounts_query = FakeAccountsQuery(still_out={(CLIENT_ID, ITEM_ID): Decimal("2")})

    with pytest.raises(InsufficientStillOutError):
        await collect_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("9")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([item]),
            movement_repo=movement_repo,
            accounts_query=accounts_query,
            uow=FakeUoW(),
        )

    assert len(movement_repo.saved) == 0  # nothing written
