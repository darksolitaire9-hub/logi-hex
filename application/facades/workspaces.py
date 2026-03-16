from domain.entities import Workspace
from domain.language import WorkspaceMode
from domain.services import create_workspace, list_workspaces
from application.facades._base import FacadeBase


class WorkspacesMixin(FacadeBase):

    async def create_workspace(
        self, name: str, mode: WorkspaceMode, owner_user_id: str
    ) -> Workspace:
        return await create_workspace(
            name=name,
            mode=mode,
            owner_user_id=owner_user_id,
            workspace_repo=self._workspace_repo,
            uow=self._uow,
        )

    async def list_workspaces(self, owner_user_id: str) -> list[Workspace]:
        return await list_workspaces(owner_user_id, self._workspace_repo)

    async def get_workspace(self, workspace_id: str) -> Workspace | None:
        return await self._workspace_repo.get_by_id(workspace_id)
