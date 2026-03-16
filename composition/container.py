"""
composition/container.py — Dependency injection wiring for logi-hex.

Builds a LogiFacade from a single AsyncSession.
Used as a FastAPI dependency via get_facade().
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.facades import LogiFacade
from infrastructure.db.config import get_session
from infrastructure.queries.accounts import SqlAlchemyAccountsQuery
from infrastructure.queries.stock import SqlAlchemyStockQuery
from infrastructure.repositories.clients import SqlAlchemyClientRepository
from infrastructure.repositories.items import (
    SqlAlchemyItemGroupRepository,
    SqlAlchemyItemRepository,
    SqlAlchemyTagRepository,
)
from infrastructure.repositories.movements import SqlAlchemyMovementRepository
from infrastructure.repositories.workspaces import SqlAlchemyWorkspaceRepository
from infrastructure.uow import SqlAlchemyUnitOfWork


async def get_facade(
    session: AsyncSession = Depends(get_session),
) -> LogiFacade:
    return LogiFacade(
        workspace_repo=SqlAlchemyWorkspaceRepository(session),
        client_repo=SqlAlchemyClientRepository(session),
        group_repo=SqlAlchemyItemGroupRepository(session),
        item_repo=SqlAlchemyItemRepository(session),
        tag_repo=SqlAlchemyTagRepository(session),
        movement_repo=SqlAlchemyMovementRepository(session),
        accounts_query=SqlAlchemyAccountsQuery(session),
        stock_query=SqlAlchemyStockQuery(session),
        uow=SqlAlchemyUnitOfWork(session),
    )
