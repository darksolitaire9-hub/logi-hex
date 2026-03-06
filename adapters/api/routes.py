# adapters/api/routes.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from application.facades import LogiFacade
from composition.container import get_facade
from domain.entities import Balance

router = APIRouter(prefix="/api")


class CreateTrackingCategoryRequest(BaseModel):
    id: str
    name: str
    enforce_returns: bool = True


class CreateTrackingItemRequest(BaseModel):
    id: str
    label: str
    category_id: str


# contianer types
class CreateContainerTypeRequest(BaseModel):
    id: str = Field(..., description="Container type ID, e.g. 'white'")
    label: str = Field(..., description="Human label, e.g. 'White Box'")


@router.get("/container-types")
async def get_container_types(facade: LogiFacade = Depends(get_facade)):
    types = await facade.list_container_types()
    return [
        {
            "id": ct.id,
            "label": ct.label,
        }
        for ct in types
    ]


@router.post("/container-types", status_code=201)
async def create_container_type(
    body: CreateContainerTypeRequest,
    facade: LogiFacade = Depends(get_facade),
):
    ct = await facade.create_container_type(type_id=body.id, label=body.label)
    return {
        "id": ct.id,
        "label": ct.label,
    }


# ---------- Request models ----------


class IssueRequest(BaseModel):
    name: str = Field(..., description="Client name, any case")
    container_type_id: str = Field(..., description="Container type ID, e.g. 'white'")
    quantity: int = Field(..., gt=0, description="How many containers issued")


class ReceiveRequest(BaseModel):
    name: str
    container_type_id: str
    quantity: int = Field(..., gt=0)


class LogContainerMovementRequest(BaseModel):
    name: str = Field(..., description="Client name")
    container_type_id: str
    quantity: int = Field(..., gt=0)
    content_type_ids: list[str] = []
    note: str | None = None


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


@router.post("/movements/issue", status_code=201)
async def issue_with_content(
    body: LogContainerMovementRequest,
    facade: LogiFacade = Depends(get_facade),
):
    tx = await facade.issue_items(
        name=body.name,
        primary_item_quantities={body.container_type_id: body.quantity},
        secondary_item_ids=body.content_type_ids,
        notes=body.note,
        primary_category_id="containers",  # later: derive from config
    )
    return {
        "transaction_id": tx.id,
        "client_id": tx.client_id,
        "client_name": tx.client_name,
        "direction": tx.direction,
        "notes": tx.notes,
        "primary_items": [
            {
                "tracking_item_id": li.tracking_item_id,
                "label": li.label,
                "quantity": li.quantity,
            }
            for li in tx.line_items
        ],
        "secondary_items": tx.secondary_items,
    }


@router.post("/movements/receive", status_code=201)
async def receive_with_content(
    body: LogContainerMovementRequest,
    facade: LogiFacade = Depends(get_facade),
):
    tx = await facade.return_items(
        name=body.name,
        primary_item_quantities={body.container_type_id: body.quantity},
        secondary_item_ids=body.content_type_ids,
        notes=body.note,
        primary_category_id="containers",
    )
    return {
        "transaction_id": tx.id,
        "client_id": tx.client_id,
        "client_name": tx.client_name,
        "direction": tx.direction,
        "notes": tx.notes,
        "primary_items": [
            {
                "tracking_item_id": li.tracking_item_id,
                "label": li.label,
                "quantity": li.quantity,
            }
            for li in tx.line_items
        ],
        "secondary_items": tx.secondary_items,
    }


@router.post("/tracking-categories", status_code=201)
async def create_tracking_category(
    body: CreateTrackingCategoryRequest,
    facade: LogiFacade = Depends(get_facade),
):
    category = await facade.create_tracking_category(
        category_id=body.id,
        name=body.name,
        enforce_returns=body.enforce_returns,
    )
    return {
        "id": category.id,
        "name": category.name,
        "enforce_returns": category.enforce_returns,
    }


@router.post("/tracking-items", status_code=201)
async def create_tracking_item(
    body: CreateTrackingItemRequest,
    facade: LogiFacade = Depends(get_facade),
):
    item = await facade.create_tracking_item(
        item_id=body.id,
        label=body.label,
        category_id=body.category_id,
    )
    return {
        "id": item.id,
        "label": item.label,
        "category_id": item.category_id,
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
