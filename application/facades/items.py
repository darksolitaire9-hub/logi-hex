from decimal import Decimal

from application.facades._base import FacadeBase
from domain.entities import Item, ItemGroup, Movement
from domain.services import (
    archive_item,
    create_item,
    create_item_group,
    create_item_with_opening_stock,
    list_item_groups,
    list_items,
    reactivate_item,
)


class ItemsMixin(FacadeBase):
    # ── Groups ────────────────────────────────────────────────────────────────

    async def create_item_group(self, workspace_id: str, name: str) -> ItemGroup:
        return await create_item_group(
            workspace_id=workspace_id,
            name=name,
            group_repo=self._group_repo,
            uow=self._uow,
        )

    async def list_item_groups(self, workspace_id: str) -> list[ItemGroup]:
        return await list_item_groups(workspace_id, self._group_repo)

    async def get_item_group(
        self, workspace_id: str, group_id: str
    ) -> ItemGroup | None:
        return await self._group_repo.get_by_id(workspace_id, group_id)

    # ── Items ─────────────────────────────────────────────────────────────────

    async def create_item(
        self,
        workspace_id: str,
        group_id: str,
        label: str,
        unit: str,
    ) -> Item:
        return await create_item(
            workspace_id=workspace_id,
            group_id=group_id,
            label=label,
            unit=unit,
            item_repo=self._item_repo,
            uow=self._uow,
        )

    async def create_item_with_opening_stock(
        self,
        workspace_id: str,
        group_id: str,
        label: str,
        unit: str,
        opening_quantity: Decimal,
    ) -> tuple[Item, Movement]:
        return await create_item_with_opening_stock(
            workspace_id=workspace_id,
            group_id=group_id,
            label=label,
            unit=unit,
            opening_quantity=opening_quantity,
            item_repo=self._item_repo,
            movement_repo=self._movement_repo,
            uow=self._uow,
        )

    async def archive_item(self, workspace_id: str, item_id: str) -> Item:
        return await archive_item(
            workspace_id=workspace_id,
            item_id=item_id,
            item_repo=self._item_repo,
            uow=self._uow,
        )

    async def reactivate_item(self, workspace_id: str, item_id: str) -> Item:
        return await reactivate_item(
            workspace_id=workspace_id,
            item_id=item_id,
            item_repo=self._item_repo,
            uow=self._uow,
        )

    async def list_items(
        self, workspace_id: str, active_only: bool = True
    ) -> list[Item]:
        return await list_items(workspace_id, self._item_repo, active_only)
