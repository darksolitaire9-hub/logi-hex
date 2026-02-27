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
    client_repo = SqlAlchemyClientRepository(session)
    container_type_repo = SqlAlchemyContainerTypeRepository(session)
    tx_repo = SqlAlchemyTransactionRepository(session)
    balance_query = SqlAlchemyBalanceQuery(session)
    summary_query = SqlAlchemySummaryQuery(session)
    uow = SqlAlchemyUnitOfWork(session)

    tracking_category_repo = SqlAlchemyTrackingCategoryRepository(session)
    tracking_item_repo = SqlAlchemyTrackingItemRepository(session)
    generic_tx_repo = SqlAlchemyGenericTransactionRepository(session)

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
