# infrastructure/queries/balances.py
from typing import List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Balance
from domain.ports import BalanceQueryPort
from infrastructure.db.tables import (
    tracking_items_table as ti,
)
from infrastructure.db.tables import (
    transaction_line_items_table as li,
)
from infrastructure.db.tables import (
    transactions_table as t,
)


class SqlAlchemyBalanceQuery(BalanceQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_balances(self) -> List[Balance]:
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
