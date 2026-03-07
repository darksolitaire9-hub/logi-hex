# infrastructure/queries/summary.py
from typing import Dict, List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities import Balance, ClientBalanceSummary
from domain.ports import SummaryQueryPort, SummaryResult
from infrastructure.db.tables import (
    tracking_items_table as ti,
)
from infrastructure.db.tables import (
    transaction_line_items_table as li,
)
from infrastructure.db.tables import (
    transactions_table as t,
)


class SqlAlchemySummaryQuery(SummaryQueryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_summary(self) -> SummaryResult:
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

        clients_map: Dict[str, ClientBalanceSummary] = {}
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
