from decimal import Decimal

import pytest

from domain.entities import Item
from domain.exceptions import (
    ArchivedItemError,
    ClientNotFoundError,
    EmptyMovementError,
    InsufficientStillOutError,
    WorkspaceModeMismatchError,
)
from domain.language import WorkspaceMode
from domain.services import collect_items
from tests.domain.conftest import (
    CLIENT_ID,
    CLIENT_NAME,
    ITEM_ID,
    ITEM_UNIT,
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
async def test_collect_exceeds_still_out_raises():
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
    assert err.client_name == CLIENT_NAME
    assert err.item_label == "Steel Box"
    assert err.unit == ITEM_UNIT


@pytest.mark.asyncio
async def test_collect_zero_still_out_raises():
    client = make_client()
    item = make_item()
    accounts_query = FakeAccountsQuery(still_out={})

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

    assert len(movement_repo.saved) == 0


@pytest.mark.asyncio
async def test_collect_wrong_mode_raises_workspace_mode_mismatch():
    client = make_client()
    item = make_item()

    with pytest.raises(WorkspaceModeMismatchError):
        await collect_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.INVENTORY,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("1")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([item]),
            movement_repo=FakeMovementRepository(),
            accounts_query=FakeAccountsQuery(
                still_out={(CLIENT_ID, ITEM_ID): Decimal("5")}
            ),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_collect_unknown_client_raises():
    other_client = make_client()
    other_client.id = "other-client"

    with pytest.raises(ClientNotFoundError):
        await collect_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("1")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(other_client),
            item_repo=FakeItemRepository([make_item()]),
            movement_repo=FakeMovementRepository(),
            accounts_query=FakeAccountsQuery(
                still_out={(CLIENT_ID, ITEM_ID): Decimal("5")}
            ),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_collect_rejects_archived_item():
    client = make_client()
    archived_item = make_item(is_active=False)

    with pytest.raises(ArchivedItemError):
        await collect_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={ITEM_ID: Decimal("1")},
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([archived_item]),
            movement_repo=FakeMovementRepository(),
            accounts_query=FakeAccountsQuery(
                still_out={(CLIENT_ID, ITEM_ID): Decimal("5")}
            ),
            uow=FakeUoW(),
        )


@pytest.mark.asyncio
async def test_collect_multi_item_one_fails_nothing_written():
    client = make_client()
    item1 = make_item()
    item2 = Item(
        id="item-002",
        workspace_id=WS_ID,
        group_id="group-001",
        label="Plastic Box",
        unit=ITEM_UNIT,
        is_active=True,
    )

    movement_repo = FakeMovementRepository()
    accounts_query = FakeAccountsQuery(
        still_out={
            (CLIENT_ID, item1.id): Decimal("5"),
            (CLIENT_ID, item2.id): Decimal("1"),
        }
    )
    uow = FakeUoW()

    with pytest.raises(InsufficientStillOutError):
        await collect_items(
            workspace_id=WS_ID,
            mode=WorkspaceMode.ACCOUNTS,
            client_id=CLIENT_ID,
            item_quantities={
                item1.id: Decimal("3"),
                item2.id: Decimal("2"),
            },
            notes=None,
            tag_ids=None,
            client_repo=FakeClientRepository(client),
            item_repo=FakeItemRepository([item1, item2]),
            movement_repo=movement_repo,
            accounts_query=accounts_query,
            uow=uow,
        )

    assert len(movement_repo.saved) == 0
    assert uow.committed is False
