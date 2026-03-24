import asyncio
import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from redis.asyncio import Redis

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

os.environ["TESTING"] = "true"
os.environ["SMTP_HOST"] = "smtp.test.com"
os.environ["SMTP_PORT"] = "465"
os.environ["SMTP_USERNAME"] = "test@test.com"
os.environ["SMTP_PASSWORD"] = "test_password"
os.environ["SMTP_FROM_EMAIL"] = "test@test.com"
os.environ["SMTP_USE_TLS"] = "True"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"
os.environ["REDIS_PASSWORD"] = ""
os.environ["REDIS_DB"] = "0"

from src.notification_service.main import app
from src.notification_service.router import AVAILABLE_PROVIDERS


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def mock_redis():
    mock = AsyncMock(spec=Redis)
    mock.ping = AsyncMock(return_value=True)
    mock.rpush = AsyncMock(return_value=1)
    mock.lpop = AsyncMock(return_value=None)
    mock.llen = AsyncMock(return_value=0)
    return mock


@pytest_asyncio.fixture
async def mock_email_provider():
    mock = AsyncMock()
    mock.provider_type = "email"
    mock.send = AsyncMock(return_value=MagicMock(success=True, message_id="test_id"))
    mock.validate_config = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_available_providers(mock_email_provider):
    with patch.dict(AVAILABLE_PROVIDERS, {"email": mock_email_provider}, clear=True):
        yield


@pytest_asyncio.fixture
async def notification_data():
    return {
        "recipient": "test@example.com",
        "provider": "email",
        "subject": "Test Notification",
        "message": "This is a test message",
    }


@pytest_asyncio.fixture
async def notification_dto(notification_data):
    from common.models.models import NotificationDTO
    return NotificationDTO(**notification_data)
