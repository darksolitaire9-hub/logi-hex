from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from application.facades import LogiFacade
from composition.container import get_facade

router = APIRouter(prefix="/api")


class LogContainerMovementRequest(BaseModel):
    name: str = Field(..., description="Client name")
    container_type_id: str
    quantity: int = Field(..., gt=0)
    content_type_ids: list[str] = []
    note: str | None = None


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
