"""
Container-related API routes.

Handles the simple/legacy container flow:
- Managing container types (create, list)
- Issuing containers to a client (OUT)
- Receiving containers back from a client (IN)

This is the original simple flow, kept separate from the richer
generic movements flow in routes_movements.py.
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


class CreateContainerTypeRequest(BaseModel):
    """Request body for creating a new container type."""

    id: str
    label: str


class IssueRequest(BaseModel):
    """Request body for issuing containers to a client (OUT)."""

    name: str
    container_type_id: str
    quantity: int = Field(..., gt=0)


class ReceiveRequest(BaseModel):
    """Request body for receiving containers back from a client (IN)."""

    name: str
    container_type_id: str
    quantity: int = Field(..., gt=0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/container-types")
async def list_container_types(facade: LogiFacade = Depends(get_facade)):
    """List all registered container types."""
    types = await facade.list_container_types()
    return [{"id": ct.id, "label": ct.label} for ct in types]


@router.post("/container-types")
async def create_container_type(
    body: CreateContainerTypeRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """Create a new container type."""
    ct = await facade.create_container_type(type_id=body.id, label=body.label)
    return {"id": ct.id, "label": ct.label}


@router.post("/issue")
async def issue_containers(
    body: IssueRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """Issue containers to a client (OUT transaction)."""
    try:
        tx = await facade.issue(
            name=body.name,
            container_type_id=body.container_type_id,
            quantity=body.quantity,
        )
    except UnknownContainerTypeError as e:
        raise HTTPException(status_code=404, detail=str(e))
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
    """Receive containers back from a client (IN transaction)."""
    try:
        tx = await facade.receive(
            name=body.name,
            container_type_id=body.container_type_id,
            quantity=body.quantity,
        )
    except UnknownContainerTypeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "transaction_id": tx.id,
        "client_id": tx.client_id,
        "client_name": tx.client_name,
        "container_type_id": tx.container_type_id,
        "direction": tx.direction,
        "quantity": tx.quantity,
    }
