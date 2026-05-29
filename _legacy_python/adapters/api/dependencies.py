from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from application.facades import LogiFacade
from domain.language import WorkspaceMode
from infrastructure.config import settings
from infrastructure.db.config import get_session
from infrastructure.queries.accounts import SqlAlchemyAccountsQuery
from infrastructure.queries.stock import SqlAlchemyStockQuery
from infrastructure.repositories.clients import SqlAlchemyClientRepository
from infrastructure.repositories.item_groups import SqlAlchemyItemGroupRepository
from infrastructure.repositories.items import SqlAlchemyItemRepository
from infrastructure.repositories.movements import SqlAlchemyMovementRepository
from infrastructure.repositories.tags import SqlAlchemyTagRepository
from infrastructure.repositories.workspaces import SqlAlchemyWorkspaceRepository
from infrastructure.uow import SqlAlchemyUnitOfWork

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        username = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise ValueError
        return username
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_facade(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(get_current_user),
) -> LogiFacade:
    """
    Build the application facade with hexagonal ports.
    One instance per request, bound to the DB session.
    """
    workspace_repo = SqlAlchemyWorkspaceRepository(session)
    client_repo = SqlAlchemyClientRepository(session)
    group_repo = SqlAlchemyItemGroupRepository(session)
    item_repo = SqlAlchemyItemRepository(session)
    tag_repo = SqlAlchemyTagRepository(session)
    movement_repo = SqlAlchemyMovementRepository(session)
    accounts_query = SqlAlchemyAccountsQuery(session)
    stock_query = SqlAlchemyStockQuery(session)
    uow = SqlAlchemyUnitOfWork(session)

    return LogiFacade(
        workspace_repo=workspace_repo,
        client_repo=client_repo,
        group_repo=group_repo,
        item_repo=item_repo,
        tag_repo=tag_repo,
        movement_repo=movement_repo,
        accounts_query=accounts_query,
        stock_query=stock_query,
        uow=uow,
    )


class WorkspaceContext:
    def __init__(self, id: str, mode: WorkspaceMode) -> None:
        self.id = id
        self.mode = mode


async def get_current_workspace(
    workspace_id: str,
    facade: LogiFacade = Depends(get_facade),
    _: str = Depends(get_current_user),
) -> WorkspaceContext:
    """
    Resolve the workspace from the path and ensure the user can access it.
    For now we only check existence; per-user access control can be added later.
    """
    workspace = await facade.get_workspace_by_id(workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    return WorkspaceContext(id=workspace.id, mode=workspace.mode)
