from decimal import Decimal

from application.facades._base import FacadeBase
from domain.entities import AccountsSummary, Movement
from domain.language import WorkspaceMode
from domain.services import collect_items, send_items


class AccountsMixin(FacadeBase):
    async def send_items(
        self,
        workspace_id: str,
        mode: WorkspaceMode,
        client_id: str,
        item_quantities: dict[str, Decimal],
        notes: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> Movement:
        return await send_items(
            workspace_id=workspace_id,
            mode=mode,
            client_id=client_id,
            item_quantities=item_quantities,
            notes=notes,
            tag_ids=tag_ids,
            client_repo=self._client_repo,
            item_repo=self._item_repo,
            movement_repo=self._movement_repo,
            uow=self._uow,
        )

    async def collect_items(
        self,
        workspace_id: str,
        mode: WorkspaceMode,
        client_id: str,
        item_quantities: dict[str, Decimal],
        notes: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> Movement:
        return await collect_items(
            workspace_id=workspace_id,
            mode=mode,
            client_id=client_id,
            item_quantities=item_quantities,
            notes=notes,
            tag_ids=tag_ids,
            client_repo=self._client_repo,
            item_repo=self._item_repo,
            movement_repo=self._movement_repo,
            accounts_query=self._accounts_query,
            uow=self._uow,
        )

    async def get_accounts_summary(self, workspace_id: str) -> AccountsSummary:
        return await self._accounts_query.get_accounts_summary(workspace_id)
