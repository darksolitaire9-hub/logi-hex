# tests/domain/test_container_services.py

import pytest

from domain import services
from domain.entities import ContainerType
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError
from tests.domain.fakes import (
    FakeBalanceQuery,
    FakeClientRepo,
    FakeContainerTypeRepo,
    FakeTxRepo,
    run,
)


def test_issue_containers_unknown_type_raises():
    client_repo = FakeClientRepo()
    container_type_repo = FakeContainerTypeRepo(types={})
    tx_repo = FakeTxRepo()

    with pytest.raises(UnknownContainerTypeError):
        run(
            services.issue_containers(
                name="Alice",
                container_type_id="white",
                quantity=3,
                client_repo=client_repo,
                container_type_repo=container_type_repo,
                tx_repo=tx_repo,
            )
        )
    assert tx_repo.saved == []


def test_issue_containers_creates_client_and_persists_tx():
    client_repo = FakeClientRepo()
    container_type_repo = FakeContainerTypeRepo(
        types={"white": ContainerType(id="white", label="White Box")}
    )
    tx_repo = FakeTxRepo()

    tx = run(
        services.issue_containers(
            name="Alice",
            container_type_id="white",
            quantity=3,
            client_repo=client_repo,
            container_type_repo=container_type_repo,
            tx_repo=tx_repo,
        )
    )

    assert len(tx_repo.saved) == 1
    saved = tx_repo.saved[0]
    assert saved.direction == "OUT"
    assert saved.container_type_id == "white"
    assert saved.quantity == 3
    assert saved.client_name == "alice"
    assert tx.id == saved.id


def test_return_containers_insufficient_balance_raises():
    client_repo = FakeClientRepo()
    container_type_repo = FakeContainerTypeRepo(
        types={"white": ContainerType(id="white", label="White Box")}
    )
    tx_repo = FakeTxRepo()
    balance_query = FakeBalanceQuery(balances={})

    with pytest.raises(InsufficientBalanceError):
        run(
            services.return_containers(
                name="Alice",
                container_type_id="white",
                quantity=1,
                client_repo=client_repo,
                container_type_repo=container_type_repo,
                tx_repo=tx_repo,
                balance_query=balance_query,
            )
        )
    assert tx_repo.saved == []


def test_return_containers_persists_in_tx_when_balance_ok():
    client_repo = FakeClientRepo()
    container_type_repo = FakeContainerTypeRepo(
        types={"white": ContainerType(id="white", label="White Box")}
    )
    tx_repo = FakeTxRepo()

    issue_tx = run(
        services.issue_containers(
            name="Alice",
            container_type_id="white",
            quantity=3,
            client_repo=client_repo,
            container_type_repo=container_type_repo,
            tx_repo=tx_repo,
        )
    )

    balance_query = FakeBalanceQuery(balances={(issue_tx.client_id, "white"): 3})

    ret_tx = run(
        services.return_containers(
            name="Alice",
            container_type_id="white",
            quantity=2,
            client_repo=client_repo,
            container_type_repo=container_type_repo,
            tx_repo=tx_repo,
            balance_query=balance_query,
        )
    )

    assert len(tx_repo.saved) == 2
    assert tx_repo.saved[1].direction == "IN"
    assert tx_repo.saved[1].quantity == 2
    assert ret_tx.direction == "IN"
