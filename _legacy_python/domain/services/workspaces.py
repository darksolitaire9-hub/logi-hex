from domain.entities import Workspace
from domain.language import WorkspaceMode
from domain.ports import UnitOfWorkPort, WorkspaceRepositoryPort


async def create_workspace(
    name: str,
    mode: WorkspaceMode,
    owner_user_id: str,
    workspace_repo: WorkspaceRepositoryPort,
    uow: UnitOfWorkPort,
) -> Workspace:
    workspace = Workspace.create(name=name, mode=mode, owner_user_id=owner_user_id)
    await workspace_repo.save(workspace)
    await uow.commit()
    return workspace


async def list_workspaces(
    owner_user_id: str,
    workspace_repo: WorkspaceRepositoryPort,
) -> list[Workspace]:
    return await workspace_repo.list_by_owner(owner_user_id)
