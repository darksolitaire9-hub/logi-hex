# infrastructure/uow.py
from sqlalchemy.ext.asyncio import AsyncSession

from domain.ports import UnitOfWorkPort


class SqlAlchemyUnitOfWork(UnitOfWorkPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
