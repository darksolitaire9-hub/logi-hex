"""
Summary and balance query API routes.

Read-only endpoints that return the current state of:
- All non-zero balances per (client, tracking item)
- Per-client summaries with grand total
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from application.facades import LogiFacade

from .dependencies import get_facade

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class BalanceResponse(BaseModel):
    client_id: str
    client_name: str
    container_type_id: str
    container_label: str
    balance: int


class ClientBalanceEntry(BaseModel):
    container_label: str
    container_type_id: str
    balance: int


class ClientSummary(BaseModel):
    client_name: str
    total_outstanding: int
    balances: list[ClientBalanceEntry]


class SummaryResponse(BaseModel):
    clients: list[ClientSummary]
    grand_total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/balances", response_model=list[BalanceResponse])
async def get_balances(facade: LogiFacade = Depends(get_facade)):
    """
    Return all non-zero balances per (client, tracking item).

    A positive balance means the client still owes that item.
    """
    balances = await facade.balances()
    return [
        BalanceResponse(
            client_id=b.client_id,
            client_name=b.client_name,
            container_type_id=b.container_type_id,
            container_label=b.container_label,
            balance=b.balance,
        )
        for b in balances
    ]


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(facade: LogiFacade = Depends(get_facade)):
    """
    Return a per-client summary of all outstanding balances.

    Includes grand_total across all clients and all item types.
    """
    result = await facade.summary()
    return SummaryResponse(
        clients=[
            ClientSummary(
                client_name=c.client_name,
                total_outstanding=c.total_outstanding,
                balances=[
                    ClientBalanceEntry(
                        container_label=b.container_label,
                        container_type_id=b.container_type_id,
                        balance=b.balance,
                    )
                    for b in c.balances
                ],
            )
            for c in result.clients
        ],
        grand_total=result.grand_total,
    )
