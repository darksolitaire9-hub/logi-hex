# tests/integration/api/conftest.py

import os
from typing import AsyncGenerator

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from adapters.api.dependencies import get_current_user, get_session
from domain.entities import Client, Item, ItemGroup, Workspace
from domain.language import WorkspaceMode
from infrastructure.db.config import create_engine
from infrastructure.db.tables import (
    clients_table,
    item_groups_table,
    items_table,
    metadata,
    workspaces_table,
)
from main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test_api.db",
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)
        await engine.dispose()


@pytest.fixture(scope="session")
def async_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def db_session(
    async_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def api_client(
    db_session: AsyncSession,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def override_get_current_user():
        return "user-123"

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Raw client — no dependency overrides. Auth is live."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def seed_workspace_graph(
    session: AsyncSession,
    mode: WorkspaceMode = WorkspaceMode.ACCOUNTS,
) -> tuple[Workspace, Client, Item]:
    """
    Shared seed helper: workspace + group + item + client.
    Available to all integration tests under tests/integration/api/.
    """
    workspace = Workspace.create(
        name="Test Workspace",
        mode=mode,
        owner_user_id="user-123",
    )
    await session.execute(
        workspaces_table.insert().values(
            id=workspace.id,
            name=workspace.name,
            mode=workspace.mode.value,
            owner_user_id=workspace.owner_user_id,
            created_at=workspace.created_at,
        )
    )

    group = ItemGroup.create(workspace_id=workspace.id, name="Containers")
    await session.execute(
        item_groups_table.insert().values(
            id=group.id,
            workspace_id=group.workspace_id,
            name=group.name,
        )
    )

    item = Item.create(
        workspace_id=workspace.id,
        group_id=group.id,
        label="Steel Box",
        unit="pcs",
    )
    await session.execute(
        items_table.insert().values(
            id=item.id,
            workspace_id=item.workspace_id,
            group_id=item.group_id,
            label=item.label,
            unit=item.unit,
            is_active=item.is_active,
        )
    )

    client = Client.create(workspace_id=workspace.id, name="Alice")
    await session.execute(
        clients_table.insert().values(
            id=client.id,
            workspace_id=client.workspace_id,
            name=client.name,
        )
    )

    await session.commit()
    return workspace, client, item
