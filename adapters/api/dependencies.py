"""
FastAPI dependency injection for the LogiFacade.

All route modules import get_facade from here, keeping
dependency wiring in one place and out of the route files.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.facades import LogiFacade
from infrastructure.sqlite_repo import (
    SqlAlchemyBalanceQuery,
    SqlAlchemyClientRepository,
    SqlAlchemyContainerTypeRepository,
    SqlAlchemyGenericTransactionRepository,
    SqlAlchemySummaryQuery,
    SqlAlchemyTrackingCategoryRepository,
    SqlAlchemyTrackingItemRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyUnitOfWork,
    get_session,
)


async def get_facade(
    session: AsyncSession = Depends(get_session),
) -> LogiFacade:
    """
    Builds and returns a LogiFacade with all repositories injected.

    Called by FastAPI's Depends() on every request that needs
    access to application logic.
    """
    return LogiFacade(
        client_repo=SqlAlchemyClientRepository(session),
        container_type_repo=SqlAlchemyContainerTypeRepository(session),
        tx_repo=SqlAlchemyTransactionRepository(session),
        balance_query=SqlAlchemyBalanceQuery(session),
        summary_query=SqlAlchemySummaryQuery(session),
        uow=SqlAlchemyUnitOfWork(session),
        tracking_category_repo=SqlAlchemyTrackingCategoryRepository(session),
        tracking_item_repo=SqlAlchemyTrackingItemRepository(session),
        generic_tx_repo=SqlAlchemyGenericTransactionRepository(session),
    )
