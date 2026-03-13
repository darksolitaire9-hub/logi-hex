"""
Shared pytest fixtures for all test layers.

conftest.py at the tests/ root means these fixtures are available
to unit/, integration/, and any future test layers automatically.
"""

import pytest
from fastapi.testclient import TestClient

from adapters.api.dependencies import get_current_user
from infrastructure.db.config import engine
from infrastructure.db.tables import metadata
from main import app

# ---------------------------------------------------------------------------
# Auth bypass: skip JWT validation in all tests
# ---------------------------------------------------------------------------


async def _fake_current_user() -> str:
    return "test-user"


app.dependency_overrides[get_current_user] = _fake_current_user


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function", autouse=True)
async def reset_db():
    """
    Drops and recreates all tables before each test function.

    This ensures every test starts with a clean, empty database,
    preventing state from leaking between tests.

    Uses the same engine as the app (SQLite), but wipes it each time.
    """
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)


@pytest.fixture()
def client():
    """
    Returns a synchronous FastAPI TestClient wrapping the main app.

    TestClient handles async route handlers transparently via anyio.
    Use this fixture in all integration/api tests to make HTTP calls
    without spinning up a real server.
    """
    return TestClient(app)
