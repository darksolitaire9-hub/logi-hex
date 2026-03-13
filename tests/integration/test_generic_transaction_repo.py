import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from domain.entities import Transaction, TransactionLineItem
from infrastructure.db.tables import (
    metadata,
    transaction_line_items_table,
    transaction_secondary_items_table,
    transactions_table,
)
from infrastructure.repositories.transactions import (
    SqlAlchemyGenericTransactionRepository,
)


@pytest.fixture
async def async_session():
    # In-memory SQLite for repo tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_by_client_id_filters_and_orders(async_session: AsyncSession):
    repo = SqlAlchemyGenericTransactionRepository(async_session)

    # Seed: 3 generic tx for client-1, 1 tx for another client,
    # and 1 old-style tx with container_type_id (should be ignored).
    base_time = datetime.now(timezone.utc)

    # Generic tx for client-1
    tx1 = Transaction(
        id="tx1",
        timestamp=base_time - timedelta(minutes=3),
        client_id="client-1",
        client_name="client one",
        direction="OUT",
        line_items=[
            TransactionLineItem(
                tracking_item_id="white",
                label="White Box",
                quantity=2,
            )
        ],
        secondary_items=["veg"],
        notes="first",
    )
    tx2 = Transaction(
        id="tx2",
        timestamp=base_time - timedelta(minutes=1),
        client_id="client-1",
        client_name="client one",
        direction="IN",
        line_items=[
            TransactionLineItem(
                tracking_item_id="white",
                label="White Box",
                quantity=1,
            )
        ],
        secondary_items=["veg"],
        notes="second",
    )
    tx3 = Transaction(
        id="tx3",
        timestamp=base_time - timedelta(minutes=2),
        client_id="client-1",
        client_name="client one",
        direction="OUT",
        line_items=[
            TransactionLineItem(
                tracking_item_id="white",
                label="White Box",
                quantity=5,
            )
        ],
        secondary_items=[],
        notes=None,
    )

    # Different client (should not show up)
    other_tx = Transaction(
        id="tx-other",
        timestamp=base_time,
        client_id="client-2",
        client_name="client two",
        direction="OUT",
        line_items=[],
        secondary_items=[],
        notes=None,
    )

    # Persist via repo.save (so auxiliary tables are filled)
    for tx in [tx1, tx2, tx3, other_tx]:
        await repo.save(tx)

    # Old-style container tx for same client (should be ignored by get_by_client_id)
    await async_session.execute(
        transactions_table.insert().values(
            id="legacy",
            timestamp=base_time + timedelta(minutes=5),
            client_id="client-1",
            client_name="client one",
            container_type_id="some-container",
            direction="OUT",
            quantity=10,
            notes=None,
        )
    )
    await async_session.commit()

    # Act
    result = await repo.get_by_client_id("client-1")

    # Assert: only tx1, tx2, tx3, ordered by timestamp DESC
    ids = [tx.id for tx in result]
    assert ids == ["tx2", "tx3", "tx1"]

    # Check line items + notes copied correctly
    tx2_loaded = result[0]
    assert tx2_loaded.notes == "second"
    assert len(tx2_loaded.line_items) == 1
    assert tx2_loaded.line_items[0].tracking_item_id == "white"
    assert tx2_loaded.line_items[0].quantity == 1
    assert tx2_loaded.secondary_items == ["veg"]
