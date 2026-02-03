import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

os.environ["TESTING"] = "true"
os.environ["USER_SERVICE_DATABASE_URL"] = "postgresql+asyncpg://admin:admin123@localhost:5432/test_user_service"

from src.user_service.main import app
from src.user_service.user_models import Base
from src.user_service.orm_utils import create_user, session_add
from src.user_service.token_utils import create_access_token, create_refresh_token
from src.user_service.user_schemes import UserSchema


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    test_db_url = os.getenv(
        "USER_SERVICE_DATABASE_URL",
        "postgresql+asyncpg://admin:admin123@localhost:5432/test_user_service"
    )
    
    engine = create_async_engine(
        test_db_url,
        echo=True,
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) 
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


@pytest_asyncio.fixture
async def test_user(async_session) -> dict:
    test_email = "test@example.com"
    test_password = "testpassword123"
    
    user = await create_user(test_email, test_password)
    await session_add(async_session, user)
    await async_session.refresh(user)
    
    return {
        "id": user.id,
        "email": test_email,
        "password": test_password,
        "user_object": user
    }


@pytest_asyncio.fixture
async def test_tokens(test_user) -> dict:
    user_schema = UserSchema(
        id=test_user["id"],
        email=test_user["email"],
        password=test_user["password"]
    )
    
    access_token = await create_access_token(user_schema)
    refresh_token = await create_refresh_token(user_schema)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }