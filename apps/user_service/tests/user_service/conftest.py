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

os.environ["TESTING"] = "true"
os.environ["TASK_SERVICE_DATABASE_URL"] = "sqlite+aiosqlite:///file::memory:?cache=shared"
os.environ["API_GATEWAY_URL"] = "http://test-api-gateway:8000"

from src.user_service.dependencies import get_session
from src.user_service.main import app
from src.user_service.orm_utils import create_user
from src.user_service.token_utils import create_access_token, create_refresh_token
from src.user_service.user_models import Base
from src.user_service.user_schemes import UserSchema


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///file::memory:?cache=shared",
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_factory = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture(autouse=True)
async def override_dependency(async_session):
    async def _override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = _override_get_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


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
    test_email = "test@example.com"
    test_password = "testpassword123"

    user = await create_user(test_email, test_password)
    await session_add(async_session, user)

    return {
        "id": user.id,
        "email": test_email,
        "password": test_password,
        "hashed_password": user.password,
        "user_object": user,
    }


@pytest_asyncio.fixture
async def test_tokens(test_user) -> dict:
    user_schema = UserSchema(
        id=test_user["id"], email=test_user["email"], password=test_user["password"]
    )

    access_token = await create_access_token(user_schema)
    refresh_token = await create_refresh_token(user_schema)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "user_id": test_user["id"],
    }


@pytest.fixture
def mock_jwt(monkeypatch):
    class MockJWT:
        def encode(self, *args, **kwargs):
            return "mock.jwt.token"

        def decode(self, *args, **kwargs):
            return {
                "sub": "1",
                "token_type": "access_token",
                "email": "test@example.com",
                "exp": 9999999999,
            }

    monkeypatch.setattr("jwt.encode", MockJWT().encode)
    monkeypatch.setattr("jwt.decode", MockJWT().decode)
