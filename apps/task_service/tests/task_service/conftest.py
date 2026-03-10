import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

os.environ["TESTING"] = "true"
os.environ["TASK_SERVICE_DATABASE_URL"] = (
    "sqlite+aiosqlite:///file::memory:?cache=shared"
)
os.environ["API_GATEWAY_URL"] = "http://test-api-gateway:8000"

from src.task_service.main import app
from src.task_service.task_models import Base, Tasks
from src.task_service.orm_utils import create_task_orm
from src.task_service.task_schemes import TaskCreateSchema


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
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
async def async_engine():
    test_db_url = os.getenv("TASK_SERVICE_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    engine = create_async_engine(
        "sqlite+aiosqlite:///file::memory:?cache=shared", echo=False, poolclass=NullPool
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
async def test_task(async_session) -> dict:
    task_data = {
        "title": "Test Task",
        "content": "This is a test task content",
        "author_id": None,
    }

    task = await create_task_orm(
        session=async_session,
        title=task_data["title"],
        content=task_data["content"],
        author_id=task_data["author_id"],
    )

    await async_session.refresh(task)

    return {
        "id": task.id,
        "title": task.title,
        "content": task.content,
        "author_id": task.author_id,
        "status": task.status,
        "task_object": task,
    }


@pytest_asyncio.fixture
async def test_task_with_author(async_session) -> dict:
    author_id = 1
    task_data = {
        "title": "Test Task with Author",
        "content": "This task has an assigned author",
        "author_id": author_id,
    }

    task = await create_task_orm(
        session=async_session,
        title=task_data["title"],
        content=task_data["content"],
        author_id=task_data["author_id"],
    )

    await async_session.refresh(task)

    return {
        "id": task.id,
        "title": task.title,
        "content": task.content,
        "author_id": task.author_id,
        "status": task.status,
        "task_object": task,
    }


@pytest_asyncio.fixture
async def multiple_tasks(async_session) -> list[dict]:
    tasks_data = [
        {"title": "Task 1", "content": "Content 1", "author_id": 1},
        {"title": "Task 2", "content": "Content 2", "author_id": 1},
        {"title": "Task 3", "content": "Content 3", "author_id": 2},
        {"title": "Task 4", "content": "Content 4", "author_id": None},
    ]

    created_tasks = []
    for task_data in tasks_data:
        task = await create_task_orm(
            session=async_session,
            title=task_data["title"],
            content=task_data["content"],
            author_id=task_data["author_id"],
        )
        await async_session.refresh(task)
        created_tasks.append(
            {
                "id": task.id,
                "title": task.title,
                "content": task.content,
                "author_id": task.author_id,
                "status": task.status,
                "task_object": task,
            }
        )

    return created_tasks


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
            if "users/with_autors/" in url or "tasks/with_autors/" in url:
                return MockResponse({"email": "test@example.com", "id": 1})
            return MockResponse({"email": "test@example.com", "id": 1})

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
