"""
Tracking bootstrap API routes.

Handles creation and management of:
- Tracking categories (e.g. "Containers", "Food")
- Tracking items within a category (e.g. "White Box", "Round Box")

These must be created before any generic movements can be issued.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from application.facades import LogiFacade

from .dependencies import get_facade

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CreateTrackingCategoryRequest(BaseModel):
    """Request body for creating a tracking category."""

    id: str
    name: str
    enforce_returns: bool = True


class CreateTrackingItemRequest(BaseModel):
    """Request body for creating a tracking item within a category."""

    id: str
    label: str
    category_id: str


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class TrackingCategoryResponse(BaseModel):
    id: str
    name: str
    enforce_returns: bool


class TrackingItemResponse(BaseModel):
    id: str
    label: str
    category_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/tracking-categories",
    status_code=201,
    response_model=TrackingCategoryResponse,
)
async def create_tracking_category(
    body: CreateTrackingCategoryRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Create a new tracking category.

    enforce_returns=True means the domain will block returns
    that exceed the issued balance for items in this category.
    """
    category = await facade.create_tracking_category(
        category_id=body.id,
        name=body.name,
        enforce_returns=body.enforce_returns,
    )
    return TrackingCategoryResponse(
        id=category.id,
        name=category.name,
        enforce_returns=category.enforce_returns,
    )


@router.post("/tracking-items", status_code=201, response_model=TrackingItemResponse)
async def create_tracking_item(
    body: CreateTrackingItemRequest,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Create a new tracking item within a category.

    The category must already exist before creating items under it.
    """
    item = await facade.create_tracking_item(
        item_id=body.id,
        label=body.label,
        category_id=body.category_id,
    )
    return TrackingItemResponse(
        id=item.id,
        label=item.label,
        category_id=item.category_id,
    )


@router.get("/tracking-items", response_model=list[TrackingItemResponse])
async def list_tracking_items(
    category_id: str,
    facade: LogiFacade = Depends(get_facade),
):
    """
    List all active tracking items within a category.

    Uses soft-delete semantics: only items with is_active=True are returned.
    """
    items = await facade.list_active_tracking_items(category_id)
    return [
        TrackingItemResponse(
            id=i.id,
            label=i.label,
            category_id=i.category_id,
        )
        for i in items
    ]


@router.delete("/tracking-items/{item_id}", status_code=204)
async def delete_tracking_item(
    item_id: str,
    facade: LogiFacade = Depends(get_facade),
):
    """
    Soft delete a tracking item.

    Marks the item as inactive so it disappears from the UI but
    remains in history.
    """
    await facade.delete_tracking_item(item_id)
