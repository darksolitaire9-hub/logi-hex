from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from application.facades import LogiFacade
from composition.container import get_facade
from domain.entities import Balance


router = APIRouter(prefix="/api", tags=["containers"])


class IssueRequest(BaseModel):
    name: str = Field(..., description="Client name, any case")
    container_type_id: str = Field(..., description="Container type ID, e.g. 'white'")
    quantity: int = Field(..., gt=0, description="How many containers issued")


class ReceiveRequest(BaseModel):
    name: str
    container_type_id: str
    quantity: int = Field(..., gt=0)


@router.post("/issue")
async def issue_containers(
    body: IssueRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Issue containers to a client (OUT).
    """
    # (Optional) could check container type exists via facade.container_type_repo
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
    body: ReceiveRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Record containers returned by a client (IN).
    """
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
async def get_balances(
    facade: LogiFacade = Depends(get_facade),
):
    """
    Get all non-zero balances per client + container type.
    """
    balances = await facade.balances()
    return balances
