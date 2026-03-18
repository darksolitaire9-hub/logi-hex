from fastapi import APIRouter, Depends, HTTPException, status

from adapters.api.dependencies import get_current_workspace, get_facade
from adapters.api.mappers.movements import movement_to_out
from adapters.api.schemas.accounts.movements_collect import CollectMovementIn
from adapters.api.schemas.movements_common import MovementOut
from adapters.api.utils.movements import aggregate_quantities, load_mapper_context
from application.facades import LogiFacade
from domain.exceptions import (
    ArchivedItemError,
    ClientNotFoundError,
    EmptyMovementError,
    InsufficientStillOutError,
    WorkspaceModeMismatchError,
)

router = APIRouter()


@router.post(
    "/collect",
    response_model=MovementOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_collect_movement(
    workspace_id: str,
    payload: CollectMovementIn,
    facade: LogiFacade = Depends(get_facade),
    workspace=Depends(get_current_workspace),
):
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one item is required.",
        )

    try:
        movement = await facade.collect_items(
            workspace_id=workspace.id,
            mode=workspace.mode,
            client_id=payload.client_id,
            item_quantities=aggregate_quantities(payload.items),
            notes=payload.notes,
            tag_ids=payload.tag_ids or [],
        )
    except EmptyMovementError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total quantity must be greater than zero.",
        )
    except ArchivedItemError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ClientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except WorkspaceModeMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except InsufficientStillOutError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    items_by_id, tags_by_id = await load_mapper_context(facade, workspace.id)
    return movement_to_out(movement, workspace.mode, items_by_id, tags_by_id)
