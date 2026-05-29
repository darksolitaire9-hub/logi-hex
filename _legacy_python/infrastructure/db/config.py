# infrastructure/db/config.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from infrastructure.config import settings

DATABASE_URL = settings.database_url


def create_engine(url: str = DATABASE_URL) -> AsyncEngine:
    return create_async_engine(url, echo=False, future=True)


engine: AsyncEngine = create_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    # Deprecated: schema is managed by Alembic migrations.
    # Kept for backwards compatibility/tests; does nothing.
    return None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
