"""
Generic rich movement API routes.

Handles the rich movement flow where:
- Primary items are tracked items (with balance enforcement)
- Secondary items are informational tags (e.g. food content types)
- Notes can be attached to each movement

This is the newer, more generic flow that replaces the simple
container-only flow for most use cases.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from application.facades import LogiFacade
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError

from .dependencies import get_facade

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class LogContainerMovementRequest(BaseModel):
    """
    Request body for a rich movement (issue or receive).

    primary_category_id identifies the category whose items are the
    primary, balance-enforced items (e.g. "containers").
    container_type_id maps to the tracking item id within that category
    (e.g. "white" in "containers" category).
    content_type_ids are informational secondary tags (no balance enforced).
    """

    name: str
    primary_category_id: str
    container_type_id: str
    quantity: int = Field(..., gt=0)
    content_type_ids: list[str] = []
    note: str | None = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class MovementPrimaryItem(BaseModel):
    tracking_item_id: str
    label: str
    quantity: int


class MovementResponse(BaseModel):
    transaction_id: str
    client_id: str
    client_name: str
    direction: str
    notes: str | None
    primary_items: list[MovementPrimaryItem]
    secondary_items: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/movements/issue", status_code=201, response_model=MovementResponse)
async def issue_movement(
    body: LogContainerMovementRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Issue items to a client (rich OUT transaction).

    Validates the primary category exists and has enforce_returns=True.
    Creates a Transaction with line items and optional secondary tags.
    """
    try:
        tx = await facade.issue_items(
            name=body.name,
            primary_item_quantities={body.container_type_id: body.quantity},
            secondary_item_ids=body.content_type_ids,
            notes=body.note,
            primary_category_id=body.primary_category_id,
        )
    except UnknownContainerTypeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return MovementResponse(
        transaction_id=tx.id,
        client_id=tx.client_id,
        client_name=tx.client_name,
        direction=tx.direction,
        notes=tx.notes,
        primary_items=[
            MovementPrimaryItem(
                tracking_item_id=li.tracking_item_id,
                label=li.label,
                quantity=li.quantity,
            )
            for li in tx.line_items
        ],
        secondary_items=list(tx.secondary_items),
    )


@router.post("/movements/receive", status_code=201, response_model=MovementResponse)
async def receive_movement(
    body: LogContainerMovementRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Receive items back from a client (rich IN transaction).

    Enforces that the client has sufficient outstanding balance
    before allowing the return.
    """
    try:
        tx = await facade.return_items(
            name=body.name,
            primary_item_quantities={body.container_type_id: body.quantity},
            secondary_item_ids=body.content_type_ids,
            notes=body.note,
            primary_category_id=body.primary_category_id,
        )
    except UnknownContainerTypeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return MovementResponse(
        transaction_id=tx.id,
        client_id=tx.client_id,
        client_name=tx.client_name,
        direction=tx.direction,
        notes=tx.notes,
        primary_items=[
            MovementPrimaryItem(
                tracking_item_id=li.tracking_item_id,
                label=li.label,
                quantity=li.quantity,
            )
            for li in tx.line_items
        ],
        secondary_items=list(tx.secondary_items),
    )
