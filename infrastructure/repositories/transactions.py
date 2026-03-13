# infrastructure/repositories/transactions.py
from typing import List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import (
    ContainerTransaction,
    Transaction,
    TransactionLineItem,
)
from domain.ports import (
    GenericTransactionRepositoryPort,
    TransactionRepositoryPort,
)
from infrastructure.db.tables import (
    transaction_line_items_table,
    transaction_secondary_items_table,
    transactions_table,
)


class SqlAlchemyTransactionRepository(TransactionRepositoryPort):
    """
    Repository for the legacy simple container flow (ContainerTransaction).
    Uses transactions_table with container_type_id and quantity on the header.
    """

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
    - transactions_table (header, with container_type_id NULL and quantity=0)
    - transaction_line_items_table (primary items and quantities)
    - transaction_secondary_items_table (secondary tags)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, tx: Transaction) -> None:
        await self.session.execute(
            transactions_table.insert().values(
                id=tx.id,
                timestamp=tx.timestamp,
                client_id=tx.client_id,
                client_name=tx.client_name,
                container_type_id=None,
                direction=tx.direction,
                quantity=0,
                notes=tx.notes,
            )
        )

        for li in tx.line_items:
            await self.session.execute(
                transaction_line_items_table.insert().values(
                    transaction_id=tx.id,
                    tracking_item_id=li.tracking_item_id,
                    label=li.label,
                    quantity=li.quantity,
                )
            )

        for secondary_id in tx.secondary_items:
            await self.session.execute(
                transaction_secondary_items_table.insert().values(
                    transaction_id=tx.id,
                    tracking_item_id=secondary_id,
                )
            )

    async def list_all(self) -> List[Transaction]:
        result = await self.session.execute(sa.select(transactions_table))
        tx_rows = result.fetchall()
        transactions: list[Transaction] = []

        for tx_row in tx_rows:
            # line items
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

            # secondary items
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
                    notes=tx_row.notes,
                )
            )

        return transactions

    async def get_by_client_id(self, client_id: str) -> List[Transaction]:
        result = await self.session.execute(
            sa.select(transactions_table)
            .where(
                transactions_table.c.client_id == client_id,
                transactions_table.c.container_type_id.is_(None),
            )
            .order_by(transactions_table.c.timestamp.desc())
        )
        tx_rows = result.fetchall()
        transactions: list[Transaction] = []

        for tx_row in tx_rows:
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
                    notes=tx_row.notes,
                )
            )

        return transactions
