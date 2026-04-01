import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared"
TEST_API_GATEWAY_URL = "http://test-api-gateway:8000"
TEST_USER_SERVICE_URL = "http://test-user-service:8000"
TEST_NOTIFICATION_URL = "http://test-notification-service:8000"

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")

os.environ.setdefault("TASK_SERVICE_DATABASE_URL", TEST_DATABASE_URL)
os.environ.setdefault("USER_SERVICE_DATABASE_URL", TEST_DATABASE_URL)
os.environ.setdefault("DATABASE_POOL_SIZE", "5")
os.environ.setdefault("DATABASE_MAX_OVERFLOW", "10")
os.environ.setdefault("DATABASE_ECHO", "false")

os.environ.setdefault("API_GATEWAY_URL", TEST_API_GATEWAY_URL)

os.environ.setdefault("ACCESS_TOKEN_EXPIRE", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE", "30")


def reset_settings_cache():
    from src.user_service.config import get_settings

    get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    reset_settings_cache()
    yield
    reset_settings_cache()


@pytest.fixture(scope="session")
def settings():
    from src.user_service.config import get_settings

    return get_settings()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    from src.user_service.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine(settings):
    from src.user_service.user_models import Base

    database_url = settings.database_url

    engine = create_async_engine(
        database_url,
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_factory = async_sessionmaker(
        db_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def override_dependencies(db_engine):
    from src.user_service.main import app
    from src.user_service.orm_utils import get_session

    async def override_get_session():
        async_session_factory = async_sessionmaker(
            db_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    yield

    app.dependency_overrides.clear()


async def session_add(session: AsyncSession, obj):
    session.add(obj)
    try:
        await session.commit()
        await session.refresh(obj)
        return obj
    except Exception:
        await session.rollback()
        raise


@pytest_asyncio.fixture
async def test_user(async_session) -> dict:
    from src.user_service.orm_utils import create_user

    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",  # pragma: allowlist secret
    }

    user = await create_user(
        email=user_data["email"],
        password=user_data["password"],
    )

    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "user_object": user,
    }


@pytest_asyncio.fixture
async def multiple_users(async_session) -> list[dict]:
    from src.user_service.orm_utils import create_user

    users_data = [
        {"email": "user1@example.com", "password": "pass1"},  # pragma: allowlist secret
        {"email": "user2@example.com", "password": "pass2"},  # pragma: allowlist secret
        {"email": "user3@example.com", "password": "pass3"},  # pragma: allowlist secret
    ]

    created_users = []
    for user_data in users_data:
        user = await create_user(
            email=user_data["email"],
            password=user_data["password"],
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)
        created_users.append(
            {
                "id": user.id,
                "email": user.email,
                "user_object": user,
            }
        )

    return created_users


@pytest.fixture
def mock_httpx_client(monkeypatch):
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error: {self.status_code}")

    class MockAsyncClient:
        def __init__(self):
            self.get_calls = []
            self.post_calls = []

        async def get(self, url, **kwargs):
            self.get_calls.append({"url": url, "kwargs": kwargs})
            return MockResponse({"status": "ok"})

        async def post(self, url, json=None, **kwargs):
            self.post_calls.append({"url": url, "json": json, "kwargs": kwargs})
            return MockResponse({"status": "sent"})

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_client = MockAsyncClient()

    def mock_async_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

    return mock_client
