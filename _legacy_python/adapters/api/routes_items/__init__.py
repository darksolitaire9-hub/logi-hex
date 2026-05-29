from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.api.dependencies import get_current_workspace, get_facade
from adapters.api.schemas.items.items import ItemIn, ItemOut
from application.facades import LogiFacade
from domain.language import WorkspaceMode

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/items",
    response_model=ItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace_item(
    workspace_id: str,
    payload: ItemIn,
    facade: LogiFacade = Depends(get_facade),
    workspace=Depends(get_current_workspace),
) -> ItemOut:
    group = await facade.get_item_group(workspace.id, payload.group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item group '{payload.group_id}' not found in this workspace.",
        )

    use_opening = (
        payload.opening_quantity is not None and payload.opening_quantity > Decimal("0")
    )

    if use_opening and workspace.mode != WorkspaceMode.INVENTORY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Opening stock is only available in Inventory mode.",
        )

    if use_opening:
        assert payload.opening_quantity is not None  # narrowed: Decimal guaranteed here
        item, _ = await facade.create_item_with_opening_stock(
            workspace_id=workspace.id,
            group_id=payload.group_id,
            label=payload.label,
            unit=payload.unit,
            opening_quantity=payload.opening_quantity,
        )
    else:
        item = await facade.create_item(
            workspace_id=workspace.id,
            group_id=payload.group_id,
            label=payload.label,
            unit=payload.unit,
        )

    return ItemOut(
        id=item.id,
        workspace_id=item.workspace_id,
        group_id=item.group_id,
        label=item.label,
        unit=item.unit,
        is_active=item.is_active,
    )
