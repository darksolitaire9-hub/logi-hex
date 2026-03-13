from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.facades import LogiFacade

from .dependencies import get_facade

router = APIRouter(prefix="/api")


class ClientResponse(BaseModel):
    id: str
    name: str


# ---------------------------------------------------------------------------
# Client transaction response models
# ---------------------------------------------------------------------------


class ClientTransactionLineItem(BaseModel):
    tracking_item_id: str
    label: str
    quantity: int


class ClientTransactionResponse(BaseModel):
    transaction_id: str
    direction: str
    timestamp: datetime
    notes: str | None
    primary_items: list[ClientTransactionLineItem]
    secondary_items: list[str]


class ClientTransactionListResponse(BaseModel):
    client_id: str
    client_name: str
    transactions: list[ClientTransactionResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(
    facade: LogiFacade = Depends(get_facade),
):
    clients = await facade.list_clients()
    return [ClientResponse(id=c.id, name=c.name) for c in clients]


@router.get(
    "/clients/{client_id}/transactions",
    response_model=ClientTransactionListResponse,
)
async def get_client_transactions(
    client_id: str,
    facade: LogiFacade = Depends(get_facade),
):
    clients = await facade.list_clients()
    client = next((c for c in clients if c.id == client_id), None)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found.")

    transactions = await facade.get_client_transactions(client_id)

    return ClientTransactionListResponse(
        client_id=client.id,
        client_name=client.name,
        transactions=[
            ClientTransactionResponse(
                transaction_id=tx.id,
                direction=tx.direction,
                timestamp=tx.timestamp,
                notes=tx.notes,
                primary_items=[
                    ClientTransactionLineItem(
                        tracking_item_id=li.tracking_item_id,
                        label=li.label,
                        quantity=li.quantity,
                    )
                    for li in tx.line_items
                ],
                secondary_items=list(tx.secondary_items),
            )
            for tx in transactions
        ],
    )
