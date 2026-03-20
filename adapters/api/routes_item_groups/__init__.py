from fastapi import APIRouter, Depends, status

from adapters.api.dependencies import get_current_workspace, get_facade
from adapters.api.schemas.items.item_groups import ItemGroupIn, ItemGroupOut
from application.facades import LogiFacade

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/item-groups",
    response_model=ItemGroupOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace_item_group(
    workspace_id: str,
    payload: ItemGroupIn,
    facade: LogiFacade = Depends(get_facade),
    workspace=Depends(get_current_workspace),
) -> ItemGroupOut:
    group = await facade.create_item_group(
        workspace_id=workspace.id,
        name=payload.name,
    )
    return ItemGroupOut(
        id=group.id,
        workspace_id=group.workspace_id,
        name=group.name,
    )
