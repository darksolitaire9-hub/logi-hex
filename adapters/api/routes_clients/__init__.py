from fastapi import APIRouter, Depends, HTTPException, status

from adapters.api.dependencies import get_current_workspace, get_facade
from adapters.api.schemas.accounts.clients import ClientOut
from application.facades import LogiFacade
from domain.language import WorkspaceMode

router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}/clients",
    response_model=list[ClientOut],
    status_code=status.HTTP_200_OK,
)
async def list_workspace_clients(
    workspace_id: str,
    facade: LogiFacade = Depends(get_facade),
    workspace=Depends(get_current_workspace),
) -> list[ClientOut]:
    if workspace.mode != WorkspaceMode.ACCOUNTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This endpoint is only available in Accounts mode.",
        )
    clients = await facade.list_clients(workspace_id=workspace.id)
    return [
        ClientOut(id=c.id, workspace_id=c.workspace_id, name=c.name) for c in clients
    ]
