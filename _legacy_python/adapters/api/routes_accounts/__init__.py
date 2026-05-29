from fastapi import APIRouter, Depends, HTTPException, status

from adapters.api.dependencies import get_current_workspace, get_facade
from adapters.api.schemas.accounts.accounts_summary import (
    AccountsSummaryOut,
    ClientStillOutOut,
    StillOutEntryOut,
)
from application.facades import LogiFacade
from domain.language import WorkspaceMode

router = APIRouter()


@router.get(
    "/workspaces/{workspace_id}/accounts",
    response_model=AccountsSummaryOut,
    status_code=status.HTTP_200_OK,
)
async def get_workspace_accounts_summary(
    workspace_id: str,
    facade: LogiFacade = Depends(get_facade),
    workspace=Depends(get_current_workspace),
) -> AccountsSummaryOut:
    if workspace.mode != WorkspaceMode.ACCOUNTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This endpoint is only available in Accounts mode.",
        )

    summary = await facade.get_accounts_summary(workspace.id)

    clients_out: list[ClientStillOutOut] = []
    for client in summary.clients:
        entries_out = [
            StillOutEntryOut(
                item_id=e.item_id,
                item_label=e.item_label,
                unit=e.unit,
                quantity=e.quantity,
            )
            for e in client.entries
        ]
        clients_out.append(
            ClientStillOutOut(
                client_id=client.client_id,
                client_name=client.client_name,
                entries=entries_out,
                total=client.total,
                is_settled=client.is_settled,
            )
        )

    return AccountsSummaryOut(
        clients=clients_out,
        grand_total=summary.grand_total,
    )
