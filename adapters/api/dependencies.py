from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from application.facades import LogiFacade
from infrastructure.config import settings
from infrastructure.db.config import get_session
from infrastructure.queries.balances import SqlAlchemyBalanceQuery
from infrastructure.queries.summary import SqlAlchemySummaryQuery
from infrastructure.repositories.clients import SqlAlchemyClientRepository
from infrastructure.repositories.container_types import (
    SqlAlchemyContainerTypeRepository,
)
from infrastructure.repositories.tracking import (
    SqlAlchemyTrackingCategoryRepository,
    SqlAlchemyTrackingItemRepository,
)
from infrastructure.repositories.transactions import (
    SqlAlchemyGenericTransactionRepository,
    SqlAlchemyTransactionRepository,
)
from infrastructure.uow import SqlAlchemyUnitOfWork

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
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
    client_repo = SqlAlchemyClientRepository(session)
    container_type_repo = SqlAlchemyContainerTypeRepository(session)
    tx_repo = SqlAlchemyTransactionRepository(session)
    generic_tx_repo = SqlAlchemyGenericTransactionRepository(session)
    tracking_category_repo = SqlAlchemyTrackingCategoryRepository(session)
    tracking_item_repo = SqlAlchemyTrackingItemRepository(session)
    balance_query = SqlAlchemyBalanceQuery(session)
    summary_query = SqlAlchemySummaryQuery(session)
    uow = SqlAlchemyUnitOfWork(session)

    return LogiFacade(
        client_repo=client_repo,
        container_type_repo=container_type_repo,
        tx_repo=tx_repo,
        balance_query=balance_query,
        summary_query=summary_query,
        uow=uow,
        tracking_category_repo=tracking_category_repo,
        tracking_item_repo=tracking_item_repo,
        generic_tx_repo=generic_tx_repo,
    )
