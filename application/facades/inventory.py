from decimal import Decimal

from application.facades._base import FacadeBase
from domain.entities import InventorySummary, Movement
from domain.language import CorrectionReason, WorkspaceMode
from domain.services import correct_stock, receive_stock, use_stock


class InventoryMixin(FacadeBase):
    async def receive_stock(
        self,
        workspace_id: str,
        mode: WorkspaceMode,
        item_id: str,
        quantity: Decimal,
        notes: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> Movement:
        return await receive_stock(
            workspace_id=workspace_id,
            mode=mode,
            item_id=item_id,
            quantity=quantity,
            notes=notes,
            tag_ids=tag_ids,
            item_repo=self._item_repo,
            movement_repo=self._movement_repo,
            uow=self._uow,
        )

    async def use_stock(
        self,
        workspace_id: str,
        mode: WorkspaceMode,
        item_id: str,
        quantity: Decimal,
        notes: str | None = None,
        tag_ids: list[str] | None = None,
    ) -> Movement:
        return await use_stock(
            workspace_id=workspace_id,
            mode=mode,
            item_id=item_id,
            quantity=quantity,
            notes=notes,
            tag_ids=tag_ids,
            item_repo=self._item_repo,
            movement_repo=self._movement_repo,
            stock_query=self._stock_query,
            uow=self._uow,
        )

    async def correct_stock(
        self,
        workspace_id: str,
        mode: WorkspaceMode,
        item_id: str,
        actual_quantity: Decimal,
        reason: CorrectionReason,
        notes: str | None = None,
    ) -> Movement:
        return await correct_stock(
            workspace_id=workspace_id,
            mode=mode,
            item_id=item_id,
            actual_quantity=actual_quantity,
            reason=reason,
            notes=notes,
            item_repo=self._item_repo,
            movement_repo=self._movement_repo,
            stock_query=self._stock_query,
            uow=self._uow,
        )

    async def get_inventory_summary(self, workspace_id: str) -> InventorySummary:
        return await self._stock_query.get_inventory_summary(workspace_id)
