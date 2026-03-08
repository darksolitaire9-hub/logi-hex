# tests/domain/test_soft_delete.py

import pytest

from application.facades import LogiFacade
from domain import services
from domain.entities import TrackingCategory, TrackingItem
from domain.exceptions import UnknownContainerTypeError
from domain.ports import UnitOfWorkPort
from tests.domain.fakes import (
    FakeBalanceQuery,
    FakeClientRepo,
    FakeContainerTypeRepo,
    FakeGenericTxRepo,
    FakeSummaryQuery,
    FakeTrackingCategoryRepo,
    FakeTrackingItemRepo,
    FakeTxRepo,
    run,
)

# ---------------------------------------------------------------------------
# Fake UOW (not in fakes.py yet — inline here for now)
# ---------------------------------------------------------------------------


class FakeUOW(UnitOfWorkPort):
    def __init__(self):
        self.committed = 0
        self.rolled_back = 0

    async def commit(self) -> None:
        self.committed += 1

    async def rollback(self) -> None:
        self.rolled_back += 1


# ---------------------------------------------------------------------------
# Helper: build a minimal facade with only tracking wired
# ---------------------------------------------------------------------------


def make_facade(item_repo: FakeTrackingItemRepo) -> LogiFacade:
    return LogiFacade(
        client_repo=FakeClientRepo(),
        container_type_repo=FakeContainerTypeRepo(),
        tx_repo=FakeTxRepo(),
        balance_query=FakeBalanceQuery(),
        summary_query=FakeSummaryQuery(),  # instead of None
        uow=FakeUOW(),
        tracking_category_repo=FakeTrackingCategoryRepo(
            categories={
                "boxes": TrackingCategory(
                    id="boxes", name="Boxes", enforce_returns=True
                )
            }
        ),
        tracking_item_repo=item_repo,
        generic_tx_repo=FakeGenericTxRepo(),
    )


# ---------------------------------------------------------------------------
# Service-level tests (no facade, direct service calls)
# ---------------------------------------------------------------------------


def test_new_item_defaults_to_active():
    item = TrackingItem(id="red", category_id="boxes", label="Red")
    assert item.is_active is True


def test_soft_delete_sets_inactive():
    item = TrackingItem(id="red", category_id="boxes", label="Red", is_active=True)
    repo = FakeTrackingItemRepo(items={"red": item})

    run(services.soft_delete_tracking_item("red", repo))

    assert repo._items["red"].is_active is False


def test_soft_delete_nonexistent_is_noop():
    repo = FakeTrackingItemRepo(items={})

    # should not raise
    run(services.soft_delete_tracking_item("ghost", repo))


def test_list_active_tracking_items_excludes_inactive():
    repo = FakeTrackingItemRepo(
        items={
            "red": TrackingItem(
                id="red", category_id="boxes", label="Red", is_active=True
            ),
            "blue": TrackingItem(
                id="blue", category_id="boxes", label="Blue", is_active=False
            ),
        }
    )

    active = run(services.list_active_tracking_items("boxes", repo))

    assert len(active) == 1
    assert active[0].id == "red"


# ---------------------------------------------------------------------------
# Facade-level tests
# ---------------------------------------------------------------------------


def test_facade_create_item_is_active():
    repo = FakeTrackingItemRepo()
    facade = make_facade(repo)

    item = run(
        facade.create_tracking_item(item_id="red", label="Red", category_id="boxes")
    )

    assert item.id == "red"
    assert item.is_active is True


def test_facade_delete_item_soft_deletes():
    repo = FakeTrackingItemRepo(
        items={
            "red": TrackingItem(
                id="red", category_id="boxes", label="Red", is_active=True
            )
        }
    )
    facade = make_facade(repo)

    run(facade.delete_tracking_item("red"))

    assert repo._items["red"].is_active is False


def test_readd_same_label_reactivates_same_id():
    repo = FakeTrackingItemRepo(
        items={
            "red": TrackingItem(
                id="red", category_id="boxes", label="Red", is_active=False
            )
        }
    )
    facade = make_facade(repo)

    # item_id="ignored" because reactivation path reuses existing id
    item = run(
        facade.create_tracking_item(item_id="ignored", label="Red", category_id="boxes")
    )

    assert item.id == "red"  # same row reactivated, not a new one
    assert item.is_active is True
    assert "ignored" not in repo._items  # no new row created


def test_readd_active_label_returns_existing():
    repo = FakeTrackingItemRepo(
        items={
            "red": TrackingItem(
                id="red", category_id="boxes", label="Red", is_active=True
            )
        }
    )
    facade = make_facade(repo)

    item = run(
        facade.create_tracking_item(item_id="ignored", label="Red", category_id="boxes")
    )

    assert item.id == "red"
    assert item.is_active is True
    assert len(repo._items) == 1  # still only one row


# ---------------------------------------------------------------------------
# Domain enforcement: inactive items blocked in movements
# ---------------------------------------------------------------------------


def test_issue_items_rejects_inactive_primary_item():
    category_repo = FakeTrackingCategoryRepo(
        categories={
            "boxes": TrackingCategory(id="boxes", name="Boxes", enforce_returns=True)
        }
    )
    item_repo = FakeTrackingItemRepo(
        items={
            "red": TrackingItem(
                id="red", category_id="boxes", label="Red", is_active=False
            )
        }
    )
    tx_repo = FakeGenericTxRepo()

    with pytest.raises(UnknownContainerTypeError):
        run(
            services.issue_items(
                name="Alice",
                primary_item_quantities={"red": 2},
                secondary_item_ids=[],
                notes=None,
                client_repo=FakeClientRepo(),
                tracking_item_repo=item_repo,
                tracking_category_repo=category_repo,
                tx_repo=tx_repo,
                balance_query=FakeBalanceQuery(),
                primary_category_id="boxes",
            )
        )

    assert tx_repo.saved == []


def test_issue_items_rejects_inactive_secondary_item():
    category_repo = FakeTrackingCategoryRepo(
        categories={
            "boxes": TrackingCategory(id="boxes", name="Boxes", enforce_returns=True)
        }
    )
    item_repo = FakeTrackingItemRepo(
        items={
            "red": TrackingItem(
                id="red", category_id="boxes", label="Red", is_active=True
            ),
            "chicken": TrackingItem(
                id="chicken", category_id="food", label="Chicken", is_active=False
            ),
        }
    )
    tx_repo = FakeGenericTxRepo()

    with pytest.raises(UnknownContainerTypeError):
        run(
            services.issue_items(
                name="Alice",
                primary_item_quantities={"red": 2},
                secondary_item_ids=["chicken"],
                notes=None,
                client_repo=FakeClientRepo(),
                tracking_item_repo=item_repo,
                tracking_category_repo=category_repo,
                tx_repo=tx_repo,
                balance_query=FakeBalanceQuery(),
                primary_category_id="boxes",
            )
        )

    assert tx_repo.saved == []


def test_return_items_rejects_inactive_primary_item():
    category_repo = FakeTrackingCategoryRepo(
        categories={
            "boxes": TrackingCategory(id="boxes", name="Boxes", enforce_returns=True)
        }
    )
    item_repo = FakeTrackingItemRepo(
        items={
            "red": TrackingItem(
                id="red", category_id="boxes", label="Red", is_active=False
            )
        }
    )
    tx_repo = FakeGenericTxRepo()

    with pytest.raises(UnknownContainerTypeError):
        run(
            services.return_items(
                name="Alice",
                primary_item_quantities={"red": 2},
                secondary_item_ids=[],
                notes=None,
                client_repo=FakeClientRepo(),
                tracking_item_repo=item_repo,
                tracking_category_repo=category_repo,
                tx_repo=tx_repo,
                balance_query=FakeBalanceQuery(balances={("cali", "red"): 5}),
                primary_category_id="boxes",
            )
        )

    assert tx_repo.saved == []
