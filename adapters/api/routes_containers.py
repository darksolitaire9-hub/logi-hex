from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from application.facades import LogiFacade
from composition.container import get_facade
from domain.entities import Balance

router = APIRouter(prefix="/api")


class CreateContainerTypeRequest(BaseModel):
    id: str = Field(..., description="Container type ID, e.g. 'white'")
    label: str = Field(..., description="Human label, e.g. 'White Box'")


@router.get("/container-types")
async def get_container_types(facade: LogiFacade = Depends(get_facade)):
    types = await facade.list_container_types()
    return [{"id": ct.id, "label": ct.label} for ct in types]


@router.post("/container-types", status_code=201)
async def create_container_type(
    body: CreateContainerTypeRequest,
    facade: LogiFacade = Depends(get_facade),
):
    ct = await facade.create_container_type(type_id=body.id, label=body.label)
    return {"id": ct.id, "label": ct.label}


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
