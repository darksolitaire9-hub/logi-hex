from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.facades import LogiFacade
from infrastructure.sqlite_repo import (
    SqlAlchemyClientRepository,
    SqlAlchemyContainerTypeRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyBalanceQuery,
    get_session,
)


async def get_facade(
    session: AsyncSession = Depends(get_session),
) -> LogiFacade:
    """
    FastAPI dependency that provides a fully wired LogiFacade.
    - Creates repositories bound to the current DB session.
    - Returns a facade that routes use cases through the domain.
    """
    client_repo = SqlAlchemyClientRepository(session)
    container_type_repo = SqlAlchemyContainerTypeRepository(session)
    tx_repo = SqlAlchemyTransactionRepository(session)
    balance_query = SqlAlchemyBalanceQuery(session)

    return LogiFacade(
        client_repo=client_repo,
        container_type_repo=container_type_repo,
        tx_repo=tx_repo,
        balance_query=balance_query,
    )
