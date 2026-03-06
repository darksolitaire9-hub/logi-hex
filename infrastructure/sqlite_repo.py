from collections.abc import AsyncGenerator
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from domain.entities import (
    Balance,
    Client,
    ClientBalanceSummary,
    ContainerTransaction,
    ContainerType,
    TrackingCategory,
    TrackingItem,
    Transaction,
    TransactionLineItem,
)
from domain.ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    GenericTransactionRepositoryPort,
    SummaryQueryPort,
    SummaryResult,
    TrackingCategoryRepositoryPort,
    TrackingItemRepositoryPort,
    TransactionRepositoryPort,
    UnitOfWorkPort,
)

# -------------------------------------------------------------------
# Engine & metadata
# -------------------------------------------------------------------

DATABASE_URL = "sqlite+aiosqlite:///logihex.db"

metadata = sa.MetaData()

clients_table = sa.Table(
    "clients",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, unique=True, nullable=False),
)

container_types_table = sa.Table(
    "container_types",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("label", sa.String, nullable=False),
)

transactions_table = sa.Table(
    "transactions",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("timestamp", sa.DateTime, nullable=False),
    sa.Column("client_id", sa.String, sa.ForeignKey("clients.id"), nullable=False),
    sa.Column("client_name", sa.String, nullable=False),
    sa.Column(
        "container_type_id",
        sa.String,
        sa.ForeignKey("container_types.id"),
        nullable=False,
    ),
    sa.Column("direction", sa.String, nullable=False),  # "OUT" or "IN"
    sa.Column("quantity", sa.Integer, nullable=False),
)


tracking_categories_table = sa.Table(
    "tracking_categories",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, nullable=False),
    sa.Column("enforce_returns", sa.Boolean, nullable=False, default=True),
)


tracking_items_table = sa.Table(
    "tracking_items",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "category_id",
        sa.String,
        sa.ForeignKey("tracking_categories.id"),
        nullable=False,
    ),
    sa.Column("label", sa.String, nullable=False),
)

transaction_line_items_table = sa.Table(
    "transaction_line_items",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "transaction_id", sa.String, sa.ForeignKey("transactions.id"), nullable=False
    ),
    sa.Column(
        "tracking_item_id",
        sa.String,
        sa.ForeignKey("tracking_items.id"),
        nullable=False,
    ),
    sa.Column("label", sa.String, nullable=False),
    sa.Column("quantity", sa.Integer, nullable=False),
)

transaction_secondary_items_table = sa.Table(
    "transaction_secondary_items",
    metadata,
    sa.Column(
        "transaction_id", sa.String, sa.ForeignKey("transactions.id"), primary_key=True
    ),
    sa.Column(
        "tracking_item_id",
        sa.String,
        sa.ForeignKey("tracking_items.id"),
        primary_key=True,
    ),
)


def create_engine() -> AsyncEngine:
    """Create the async SQLAlchemy engine for SQLite."""
    return create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
    )


engine: AsyncEngine = create_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-friendly session dependency."""
    async with SessionLocal() as session:
        yield session


# -------------------------------------------------------------------
# Repositories implementing ports
# -------------------------------------------------------------------


class SqlAlchemyClientRepository(ClientRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_by_name(self, name: str) -> Client:
        normalized = name.lower().strip()
        result = await self.session.execute(
            sa.select(clients_table).where(clients_table.c.name == normalized)
        )
        row = result.first()  # Row | None
        if row is not None:
            return Client(id=row.id, name=row.name)

        client = Client.from_name(name)
        await self.session.execute(
            clients_table.insert().values(id=client.id, name=client.name)
        )
        return client

    async def list_all(self) -> List[Client]:
        result = await self.session.execute(sa.select(clients_table))
        rows = result.fetchall()
        return [Client(id=row.id, name=row.name) for row in rows]


class SqlAlchemyContainerTypeRepository(ContainerTypeRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[ContainerType]:
        result = await self.session.execute(sa.select(container_types_table))
        rows = result.fetchall()
        return [ContainerType(id=row.id, label=row.label) for row in rows]

    async def get_by_id(self, type_id: str) -> Optional[ContainerType]:
        result = await self.session.execute(
            sa.select(container_types_table).where(
                container_types_table.c.id == type_id
            )
        )
        row = result.first()
        if row is None:
            return None
        # row is a Row, its columns are accessible as attributes
        return ContainerType(id=row.id, label=row.label)

    async def save(self, container_type: ContainerType) -> None:
        # First check if it exists
        existing = await self.get_by_id(container_type.id)
        if existing is None:
            # Insert
            await self.session.execute(
                container_types_table.insert().values(
                    id=container_type.id,
                    label=container_type.label,
                )
            )
        else:
            # Update
            await self.session.execute(
                sa.update(container_types_table)
                .where(container_types_table.c.id == container_type.id)
                .values(label=container_type.label)
            )

    async def delete(self, type_id: str) -> None:
        await self.session.execute(
            sa.delete(container_types_table).where(
                container_types_table.c.id == type_id
            )
        )


class SqlAlchemyTrackingCategoryRepository(TrackingCategoryRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> List[TrackingCategory]:
        result = await self.session.execute(sa.select(tracking_categories_table))
        rows = result.fetchall()
        return [
            TrackingCategory(
                id=row.id,
                name=row.name,
                enforce_returns=row.enforce_returns,
            )
            for row in rows
        ]

    async def get_by_id(self, category_id: str) -> Optional[TrackingCategory]:
        result = await self.session.execute(
            sa.select(tracking_categories_table).where(
                tracking_categories_table.c.id == category_id
            )
        )
        row = result.first()
        if row is None:
            return None
        return TrackingCategory(
            id=row.id,
            name=row.name,
            enforce_returns=row.enforce_returns,
        )

    async def save(self, category: TrackingCategory) -> None:
        existing = await self.get_by_id(category.id)
        if existing is None:
            await self.session.execute(
                tracking_categories_table.insert().values(
                    id=category.id,
                    name=category.name,
                    enforce_returns=category.enforce_returns,
                )
            )
        else:
            await self.session.execute(
                sa.update(tracking_categories_table)
                .where(tracking_categories_table.c.id == category.id)
                .values(
                    name=category.name,
                    enforce_returns=category.enforce_returns,
                )
            )

    async def delete(self, category_id: str) -> None:
        await self.session.execute(
            sa.delete(tracking_categories_table).where(
                tracking_categories_table.c.id == category_id
            )
        )


class SqlAlchemyTrackingItemRepository(TrackingItemRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all_by_category(self, category_id: str) -> List[TrackingItem]:
        result = await self.session.execute(
            sa.select(tracking_items_table).where(
                tracking_items_table.c.category_id == category_id
            )
        )
        rows = result.fetchall()
        return [
            TrackingItem(
                id=row.id,
                category_id=row.category_id,
                label=row.label,
            )
            for row in rows
        ]

    async def get_by_id(self, item_id: str) -> Optional[TrackingItem]:
        result = await self.session.execute(
            sa.select(tracking_items_table).where(tracking_items_table.c.id == item_id)
        )
        row = result.first()
        if row is None:
            return None
        return TrackingItem(
            id=row.id,
            category_id=row.category_id,
            label=row.label,
        )

    async def save(self, item: TrackingItem) -> None:
        existing = await self.get_by_id(item.id)
        if existing is None:
            await self.session.execute(
                tracking_items_table.insert().values(
                    id=item.id,
                    category_id=item.category_id,
                    label=item.label,
                )
            )
        else:
            await self.session.execute(
                sa.update(tracking_items_table)
                .where(tracking_items_table.c.id == item.id)
                .values(
                    category_id=item.category_id,
                    label=item.label,
                )
            )

    async def delete(self, item_id: str) -> None:
        await self.session.execute(
            sa.delete(tracking_items_table).where(tracking_items_table.c.id == item_id)
        )


class SqlAlchemyTransactionRepository(TransactionRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, tx: ContainerTransaction) -> None:
        await self.session.execute(
            transactions_table.insert().values(
                id=tx.id,
                timestamp=tx.timestamp,
                client_id=tx.client_id,
                client_name=tx.client_name,
                container_type_id=tx.container_type_id,
                direction=tx.direction,
                quantity=tx.quantity,
            )
        )

    async def list_all(self) -> List[ContainerTransaction]:
        result = await self.session.execute(sa.select(transactions_table))
        rows = result.fetchall()
        return [
            ContainerTransaction(
                id=row.id,
                timestamp=row.timestamp,
                client_id=row.client_id,
                client_name=row.client_name,
                container_type_id=row.container_type_id,
                direction=row.direction,
                quantity=row.quantity,
            )
            for row in rows
        ]


class SqlAlchemyGenericTransactionRepository(GenericTransactionRepositoryPort):
    """
    Persists the generic Transaction aggregate into:
    - transactions_table (header)
    - transaction_line_items_table
    - transaction_secondary_items_table
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, tx: Transaction) -> None:
        # Insert header into existing transactions_table
        await self.session.execute(
            transactions_table.insert().values(
                id=tx.id,
                timestamp=tx.timestamp,
                client_id=tx.client_id,
                client_name=tx.client_name,
                container_type_id="",  # legacy column; not used for generic model
                direction=tx.direction,
                quantity=0,  # legacy column; detailed in line items
            )
        )

        # Insert line items
        for li in tx.line_items:
            await self.session.execute(
                transaction_line_items_table.insert().values(
                    transaction_id=tx.id,
                    tracking_item_id=li.tracking_item_id,
                    label=li.label,
                    quantity=li.quantity,
                )
            )

        # Insert secondary items
        for secondary_id in tx.secondary_items:
            await self.session.execute(
                transaction_secondary_items_table.insert().values(
                    transaction_id=tx.id,
                    tracking_item_id=secondary_id,
                )
            )

    async def list_all(self) -> List[Transaction]:
        # Fetch all transaction headers
        result = await self.session.execute(sa.select(transactions_table))
        tx_rows = result.fetchall()
        transactions: list[Transaction] = []

        for tx_row in tx_rows:
            # Load line items
            li_result = await self.session.execute(
                sa.select(transaction_line_items_table).where(
                    transaction_line_items_table.c.transaction_id == tx_row.id
                )
            )
            li_rows = li_result.fetchall()
            line_items = [
                TransactionLineItem(
                    tracking_item_id=li_row.tracking_item_id,
                    label=li_row.label,
                    quantity=li_row.quantity,
                )
                for li_row in li_rows
            ]

            # Load secondary items
            sec_result = await self.session.execute(
                sa.select(transaction_secondary_items_table.c.tracking_item_id).where(
                    transaction_secondary_items_table.c.transaction_id == tx_row.id
                )
            )
            secondary_items = [row.tracking_item_id for row in sec_result.fetchall()]

            transactions.append(
                Transaction(
                    id=tx_row.id,
                    timestamp=tx_row.timestamp,
                    client_id=tx_row.client_id,
                    client_name=tx_row.client_name,
                    direction=tx_row.direction,
                    line_items=line_items,
                    secondary_items=secondary_items,
                    notes=None,  # notes column to be added later if needed
                )
            )

        return transactions


class SqlAlchemyBalanceQuery(BalanceQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_balances(self) -> List[Balance]:
        t = transactions_table
        li = transaction_line_items_table
        ti = tracking_items_table

        out_qty = sa.case((t.c.direction == "OUT", li.c.quantity), else_=0)
        in_qty = sa.case((t.c.direction == "IN", li.c.quantity), else_=0)
        balance_expr = sa.func.sum(out_qty - in_qty)

        stmt = (
            sa.select(
                t.c.client_id,
                sa.func.max(t.c.client_name).label("client_name"),
                li.c.tracking_item_id.label("container_type_id"),
                sa.func.max(ti.c.label).label("container_label"),
                balance_expr.label("balance"),
            )
            .join(li, li.c.transaction_id == t.c.id)
            .join(ti, ti.c.id == li.c.tracking_item_id, isouter=True)
            .group_by(t.c.client_id, li.c.tracking_item_id)
        )

        rows = (await self.session.execute(stmt)).fetchall()
        return [
            Balance(
                client_id=row.client_id,
                client_name=row.client_name,
                container_type_id=row.container_type_id,
                container_label=row.container_label or row.container_type_id,
                balance=row.balance,
            )
            for row in rows
            if row.balance != 0
        ]

    async def get_balance_for(self, client_id: str, tracking_item_id: str) -> int:
        t = transactions_table
        li = transaction_line_items_table

        out_qty = sa.case((t.c.direction == "OUT", li.c.quantity), else_=0)
        in_qty = sa.case((t.c.direction == "IN", li.c.quantity), else_=0)
        balance_expr = sa.func.sum(out_qty - in_qty)

        stmt = (
            sa.select(balance_expr)
            .select_from(t)
            .join(li, li.c.transaction_id == t.c.id)
            .where(
                t.c.client_id == client_id,
                li.c.tracking_item_id == tracking_item_id,
            )
        )

        value = (await self.session.execute(stmt)).scalar()
        return value or 0


class SqlAlchemySummaryQuery(SummaryQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_summary(self) -> SummaryResult:
        t = transactions_table
        li = transaction_line_items_table
        ti = tracking_items_table

        out_qty = sa.case((t.c.direction == "OUT", li.c.quantity), else_=0)
        in_qty = sa.case((t.c.direction == "IN", li.c.quantity), else_=0)
        balance_expr = sa.func.sum(out_qty - in_qty)

        stmt = (
            sa.select(
                t.c.client_id,
                sa.func.max(t.c.client_name).label("client_name"),
                li.c.tracking_item_id.label("container_type_id"),
                sa.func.max(ti.c.label).label("container_label"),
                balance_expr.label("balance"),
            )
            .join(li, li.c.transaction_id == t.c.id)
            .join(ti, ti.c.id == li.c.tracking_item_id, isouter=True)
            .group_by(t.c.client_id, li.c.tracking_item_id)
        )

        rows = (await self.session.execute(stmt)).fetchall()

        clients_map: dict[str, ClientBalanceSummary] = {}
        for row in rows:
            if row.balance == 0:
                continue

            b = Balance(
                client_id=row.client_id,
                client_name=row.client_name,
                container_type_id=row.container_type_id,
                container_label=row.container_label or row.container_type_id,
                balance=row.balance,
            )

            if row.client_id not in clients_map:
                clients_map[row.client_id] = ClientBalanceSummary(
                    client_id=row.client_id,
                    client_name=row.client_name,
                    total_outstanding=0,
                    balances=[],
                )

            clients_map[row.client_id].balances.append(b)
            clients_map[row.client_id].total_outstanding += row.balance

        clients = list(clients_map.values())
        return SummaryResult(
            clients=clients,
            grand_total=sum(c.total_outstanding for c in clients),
        )


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
