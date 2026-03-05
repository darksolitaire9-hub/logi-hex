# adapters/api/routes.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from application.facades import LogiFacade
from composition.container import get_facade
from domain.entities import Balance, ContainerType

router = APIRouter(prefix="/api")


# ---------- Request models ----------


class IssueRequest(BaseModel):
    name: str = Field(..., description="Client name, any case")
    container_type_id: str = Field(..., description="Container type ID, e.g. 'white'")
    quantity: int = Field(..., gt=0, description="How many containers issued")


class ReceiveRequest(BaseModel):
    name: str
    container_type_id: str
    quantity: int = Field(..., gt=0)


# ---------- Core JSON API endpoints ----------


@router.post("/issue")
async def issue_containers(
    body: IssueRequest, facade: LogiFacade = Depends(get_facade)
):
    tx = await facade.issue(
        name=body.name,
        container_type_id=body.container_type_id,
        quantity=body.quantity,
    )
    return {
        "transaction_id": tx.id,
        "client_id": tx.client_id,
        "client_name": tx.client_name,
        "container_type_id": tx.container_type_id,
        "direction": tx.direction,
        "quantity": tx.quantity,
    }


@router.post("/receive")
async def receive_containers(
    body: ReceiveRequest, facade: LogiFacade = Depends(get_facade)
):
    tx = await facade.receive(
        name=body.name,
        container_type_id=body.container_type_id,
        quantity=body.quantity,
    )
    return {
        "transaction_id": tx.id,
        "client_id": tx.client_id,
        "client_name": tx.client_name,
        "container_type_id": tx.container_type_id,
        "direction": tx.direction,
        "quantity": tx.quantity,
    }


@router.get("/balances", response_model=list[Balance])
async def get_balances(facade: LogiFacade = Depends(get_facade)):
    return await facade.balances()


@router.get("/summary")
async def get_summary(facade: LogiFacade = Depends(get_facade)):
    result = await facade.summary()
    return {
        "clients": [
            {
                "client_name": c.client_name,
                "total_outstanding": c.total_outstanding,
                "balances": [
                    {
                        "container_label": b.container_label,
                        "container_type_id": b.container_type_id,
                        "balance": b.balance,
                    }
                    for b in c.balances
                ],
            }
            for c in result.clients
        ],
        "grand_total": result.grand_total,
    }
