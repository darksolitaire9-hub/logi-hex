from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.facades import LogiFacade
from infrastructure.sqlite_repo import (
    SqlAlchemyBalanceQuery,
    SqlAlchemyClientRepository,
    SqlAlchemyContainerTypeRepository,
    SqlAlchemySummaryQuery,
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
    uow = SqlAlchemyUnitOfWork(session)

    return LogiFacade(
        client_repo=client_repo,
        container_type_repo=container_type_repo,
        tx_repo=tx_repo,
        balance_query=balance_query,
        summary_query=SqlAlchemySummaryQuery(session),
        uow=uow,
    )
