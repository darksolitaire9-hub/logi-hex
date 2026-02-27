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
)
from domain.ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    SummaryQueryPort,
    SummaryResult,
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


class SqlAlchemyBalanceQuery(BalanceQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_balances(self) -> List[Balance]:
        # OUT adds to balance (client owes more), IN subtracts (they return)
        out_case = sa.case(
            (transactions_table.c.direction == "OUT", transactions_table.c.quantity),
            else_=0,
        )

        in_case = sa.case(
            (transactions_table.c.direction == "IN", transactions_table.c.quantity),
            else_=0,
        )

        # balance = SUM(OUT - IN)
        balance_expr = sa.func.sum(out_case - in_case)

        stmt = (
            sa.select(
                transactions_table.c.client_id.label("client_id"),
                sa.func.max(transactions_table.c.client_name).label("client_name"),
                transactions_table.c.container_type_id.label("container_type_id"),
                sa.func.max(container_types_table.c.label).label("container_label"),
                balance_expr.label("balance"),
            )
            .join(
                container_types_table,
                container_types_table.c.id == transactions_table.c.container_type_id,
                isouter=True,  # LEFT OUTER JOIN for robustness
            )
            .group_by(
                transactions_table.c.client_id,
                transactions_table.c.container_type_id,
            )
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        balances: List[Balance] = []
        for row in rows:
            if row.balance == 0:
                continue
            balances.append(
                Balance(
                    client_id=row.client_id,
                    client_name=row.client_name,
                    container_type_id=row.container_type_id,
                    container_label=row.container_label or row.container_type_id,
                    balance=row.balance,
                )
            )
        return balances

    async def get_balance_for(self, client_id: str, container_type_id: str) -> int:
        # used by domain service to validate `/receive`
        out_case = sa.case(
            (transactions_table.c.direction == "OUT", transactions_table.c.quantity),
            else_=0,
        )
        in_case = sa.case(
            (transactions_table.c.direction == "IN", transactions_table.c.quantity),
            else_=0,
        )

        balance_expr = sa.func.sum(out_case - in_case)  # OUT - IN

        stmt = sa.select(balance_expr).where(
            transactions_table.c.client_id == client_id,
            transactions_table.c.container_type_id == container_type_id,
        )

        result = await self.session.execute(stmt)
        value = result.scalar()
        return value or 0  # treat no rows as 0


# infrastructure/sqlite_repo.py  (add after SqlAlchemyBalanceQuery)


class SqlAlchemySummaryQuery(SummaryQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_summary(self) -> SummaryResult:
        out_case = sa.case(
            (transactions_table.c.direction == "OUT", transactions_table.c.quantity),
            else_=0,
        )
        in_case = sa.case(
            (transactions_table.c.direction == "IN", transactions_table.c.quantity),
            else_=0,
        )
        balance_expr = sa.func.sum(out_case - in_case)

        stmt = (
            sa.select(
                transactions_table.c.client_id.label("client_id"),
                sa.func.max(transactions_table.c.client_name).label("client_name"),
                transactions_table.c.container_type_id.label("container_type_id"),
                sa.func.max(container_types_table.c.label).label("container_label"),
                balance_expr.label("balance"),
            )
            .join(
                container_types_table,
                container_types_table.c.id == transactions_table.c.container_type_id,
                isouter=True,
            )
            .group_by(
                transactions_table.c.client_id,
                transactions_table.c.container_type_id,
            )
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        # group rows by client
        clients_map: dict[str, ClientBalanceSummary] = {}
        for row in rows:
            if row.balance == 0:
                continue

            balance = Balance(
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

            clients_map[row.client_id].balances.append(balance)
            clients_map[row.client_id].total_outstanding += row.balance

        clients = list(clients_map.values())
        grand_total = sum(c.total_outstanding for c in clients)

        return SummaryResult(clients=clients, grand_total=grand_total)


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
