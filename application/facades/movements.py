from application.facades._base import FacadeBase
from domain.entities import Movement


class MovementsMixin(FacadeBase):
    async def list_movements(self, workspace_id: str) -> list[Movement]:
        return await self._movement_repo.list_by_workspace(workspace_id)

    async def list_movements_by_client(
        self, workspace_id: str, client_id: str
    ) -> list[Movement]:
        return await self._movement_repo.list_by_client(workspace_id, client_id)

    async def list_movements_by_item(
        self, workspace_id: str, item_id: str
    ) -> list[Movement]:
        return await self._movement_repo.list_by_item(workspace_id, item_id)
