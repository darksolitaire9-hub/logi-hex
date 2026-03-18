from decimal import Decimal

import pytest

from domain.language import MovementDirection, WorkspaceMode
from domain.services import collect_items
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
async def test_collect_within_still_out_succeeds():
    client = make_client()
    item = make_item()
    movement_repo = FakeMovementRepository()
    uow = FakeUoW()

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
