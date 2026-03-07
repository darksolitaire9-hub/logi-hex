# tests/domain/test_item_services.py

import pytest

from domain import services
from domain.entities import TrackingCategory, TrackingItem
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError
from tests.domain.fakes import (
    FakeBalanceQuery,
    FakeClientRepo,
    FakeGenericTxRepo,
    FakeTrackingCategoryRepo,
    FakeTrackingItemRepo,
    run,
)


def test_issue_items_invalid_primary_category_raises():
    client_repo = FakeClientRepo()
    tracking_item_repo = FakeTrackingItemRepo()
    tracking_category_repo = FakeTrackingCategoryRepo(categories={})
    tx_repo = FakeGenericTxRepo()
    balance_query = FakeBalanceQuery()

    with pytest.raises(UnknownContainerTypeError):
        run(
            services.issue_items(
                name="Alice",
                primary_item_quantities={"white": 3},
                secondary_item_ids=[],
                notes=None,
                client_repo=client_repo,
                tracking_item_repo=tracking_item_repo,
                tracking_category_repo=tracking_category_repo,
                tx_repo=tx_repo,
                balance_query=balance_query,
                primary_category_id="containers",
            )
        )
    assert tx_repo.saved == []


def test_issue_items_invalid_tracking_item_raises():
    client_repo = FakeClientRepo()
    tracking_category_repo = FakeTrackingCategoryRepo(
        categories={
            "containers": TrackingCategory(
                id="containers", name="Containers", enforce_returns=True
            )
        }
    )
    tracking_item_repo = FakeTrackingItemRepo(items={})
    tx_repo = FakeGenericTxRepo()
    balance_query = FakeBalanceQuery()

    with pytest.raises(UnknownContainerTypeError):
        run(
            services.issue_items(
                name="Alice",
                primary_item_quantities={"white": 3},
                secondary_item_ids=[],
                notes=None,
                client_repo=client_repo,
                tracking_item_repo=tracking_item_repo,
                tracking_category_repo=tracking_category_repo,
                tx_repo=tx_repo,
                balance_query=balance_query,
                primary_category_id="containers",
            )
        )
    assert tx_repo.saved == []


def test_issue_items_all_zero_quantities_raises_value_error():
    client_repo = FakeClientRepo()
    tracking_category_repo = FakeTrackingCategoryRepo(
        categories={
            "containers": TrackingCategory(
                id="containers", name="Containers", enforce_returns=True
            )
        }
    )
    tracking_item_repo = FakeTrackingItemRepo(
        items={
            "white": TrackingItem(
                id="white", category_id="containers", label="White Box"
            )
        }
    )
    tx_repo = FakeGenericTxRepo()
    balance_query = FakeBalanceQuery()

    with pytest.raises(ValueError):
        run(
            services.issue_items(
                name="Alice",
                primary_item_quantities={"white": 0},
                secondary_item_ids=[],
                notes=None,
                client_repo=client_repo,
                tracking_item_repo=tracking_item_repo,
                tracking_category_repo=tracking_category_repo,
                tx_repo=tx_repo,
                balance_query=balance_query,
                primary_category_id="containers",
            )
        )
    assert tx_repo.saved == []


def test_issue_items_creates_out_transaction_with_line_items():
    client_repo = FakeClientRepo()
    tracking_category_repo = FakeTrackingCategoryRepo(
        categories={
            "containers": TrackingCategory(
                id="containers", name="Containers", enforce_returns=True
            )
        }
    )
    tracking_item_repo = FakeTrackingItemRepo(
        items={
            "white": TrackingItem(
                id="white", category_id="containers", label="White Box"
            )
        }
    )
    tx_repo = FakeGenericTxRepo()
    balance_query = FakeBalanceQuery()

    tx = run(
        services.issue_items(
            name="Alice",
            primary_item_quantities={"white": 3},
            secondary_item_ids=["veg"],
            notes="Lunch",
            client_repo=client_repo,
            tracking_item_repo=tracking_item_repo,
            tracking_category_repo=tracking_category_repo,
            tx_repo=tx_repo,
            balance_query=balance_query,
            primary_category_id="containers",
        )
    )

    assert len(tx_repo.saved) == 1
    saved = tx_repo.saved[0]
    assert saved.direction == "OUT"
    assert len(saved.line_items) == 1
    li = saved.line_items[0]
    assert li.tracking_item_id == "white"
    assert li.quantity == 3
    assert saved.secondary_items == ["veg"]
    assert saved.notes == "Lunch"
    assert tx.id == saved.id


def test_return_items_insufficient_balance_raises():
    client_repo = FakeClientRepo()
    tracking_category_repo = FakeTrackingCategoryRepo(
        categories={
            "containers": TrackingCategory(
                id="containers", name="Containers", enforce_returns=True
            )
        }
    )
    tracking_item_repo = FakeTrackingItemRepo(
        items={
            "white": TrackingItem(
                id="white", category_id="containers", label="White Box"
            )
        }
    )
    tx_repo = FakeGenericTxRepo()
    balance_query = FakeBalanceQuery(balances={})

    with pytest.raises(InsufficientBalanceError):
        run(
            services.return_items(
                name="Alice",
                primary_item_quantities={"white": 1},
                secondary_item_ids=[],
                notes=None,
                client_repo=client_repo,
                tracking_item_repo=tracking_item_repo,
                tracking_category_repo=tracking_category_repo,
                tx_repo=tx_repo,
                balance_query=balance_query,
                primary_category_id="containers",
            )
        )
    assert tx_repo.saved == []


def test_return_items_creates_in_transaction_when_balance_ok():
    client_repo = FakeClientRepo()
    tracking_category_repo = FakeTrackingCategoryRepo(
        categories={
            "containers": TrackingCategory(
                id="containers", name="Containers", enforce_returns=True
            )
        }
    )
    tracking_item_repo = FakeTrackingItemRepo(
        items={
            "white": TrackingItem(
                id="white", category_id="containers", label="White Box"
            )
        }
    )
    tx_repo = FakeGenericTxRepo()

    issue_tx = run(
        services.issue_items(
            name="Alice",
            primary_item_quantities={"white": 3},
            secondary_item_ids=[],
            notes=None,
            client_repo=client_repo,
            tracking_item_repo=tracking_item_repo,
            tracking_category_repo=tracking_category_repo,
            tx_repo=tx_repo,
            balance_query=FakeBalanceQuery(),
            primary_category_id="containers",
        )
    )

    balance_query = FakeBalanceQuery(balances={(issue_tx.client_id, "white"): 3})

    ret_tx = run(
        services.return_items(
            name="Alice",
            primary_item_quantities={"white": 2},
            secondary_item_ids=["veg"],
            notes="Returned boxes",
            client_repo=client_repo,
            tracking_item_repo=tracking_item_repo,
            tracking_category_repo=tracking_category_repo,
            tx_repo=tx_repo,
            balance_query=balance_query,
            primary_category_id="containers",
        )
    )

    assert len(tx_repo.saved) == 2
    assert tx_repo.saved[1].direction == "IN"
    assert tx_repo.saved[1].line_items[0].quantity == 2
    assert tx_repo.saved[1].secondary_items == ["veg"]
    assert tx_repo.saved[1].notes == "Returned boxes"
    assert ret_tx.direction == "IN"
