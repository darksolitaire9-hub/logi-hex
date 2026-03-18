from fastapi import APIRouter, Depends, HTTPException, status

from adapters.api.dependencies import get_current_workspace, get_facade
from adapters.api.mappers.movements import movement_to_out
from adapters.api.schemas.inventory.movements_correct import CorrectMovementIn
from adapters.api.schemas.movements_common import MovementOut
from adapters.api.utils.movements import load_mapper_context
from application.facades import LogiFacade
from domain.exceptions import (
    ArchivedItemError,
    CorrectionReasonRequiredError,
    ItemNotFoundError,
    WorkspaceModeMismatchError,
)

router = APIRouter()


@router.post(
    "/correct",
    response_model=MovementOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_correct_movement(
    workspace_id: str,
    payload: CorrectMovementIn,
    facade: LogiFacade = Depends(get_facade),
    workspace=Depends(get_current_workspace),
):
    try:
        movement = await facade.correct_stock(
            workspace_id=workspace.id,
            mode=workspace.mode,
            item_id=payload.item_id,
            actual_quantity=payload.actual_quantity,
            reason=payload.reason,
            notes=payload.notes,
        )
    except ArchivedItemError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except CorrectionReasonRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except ItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except WorkspaceModeMismatchError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    items_by_id, tags_by_id = await load_mapper_context(facade, workspace.id)
    return movement_to_out(movement, workspace.mode, items_by_id, tags_by_id)
