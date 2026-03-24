import asyncio
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

os.environ["TESTING"] = "true"
os.environ["USER_URL"] = "http://test-user-service:8000"
os.environ["TASK_URL"] = "http://test-task-service:8000"
os.environ["NOTIFICATION_URL"] = "http://test-notification-service:8000"
os.environ["ANALYTICS_URL"] = "http://test-analytic-service:8000"

from src.api_gateway.main import app


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


@pytest.fixture
def mock_httpx_client():
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.text = json_data if isinstance(json_data, str) else str(json_data)

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error: {self.status_code}")

    class MockAsyncClient:
        def __init__(self):
            self.get_calls = []
            self.post_calls = []
            self.timeout = None

        async def get(self, url, **kwargs):
            self.get_calls.append({"url": url, "kwargs": kwargs})
            if "receive_user_by_id" in url:
                return MockResponse({"email": "test@example.com", "id": 1})
            return MockResponse({})

        async def post(self, url, json=None, **kwargs):
            self.post_calls.append({"url": url, "json": json, "kwargs": kwargs})
            if "send_notification" in url:
                return MockResponse({"status": "queued", "queued": True})
            return MockResponse({})

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_client = MockAsyncClient()

    return mock_client


@pytest.fixture
def mock_httpx_client_error():
    class MockResponse:
        def __init__(self, status_code=500, text="Internal Server Error"):
            self.status_code = status_code
            self.text = text

        def json(self):
            return {}

    class MockAsyncClient:
        def __init__(self):
            self.get_calls = []
            self.post_calls = []

        async def get(self, url, **kwargs):
            self.get_calls.append({"url": url, "kwargs": kwargs})
            return MockResponse(status_code=500, text="User service error")

        async def post(self, url, json=None, **kwargs):
            self.post_calls.append({"url": url, "json": json, "kwargs": kwargs})
            return MockResponse(status_code=500, text="Notification service error")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockAsyncClient()


@pytest.fixture
def mock_httpx_client_unexpected_response():
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            self.text = str(json_data)

        def json(self):
            return self.json_data

    class MockAsyncClient:
        def __init__(self):
            self.post_calls = []

        async def post(self, url, json=None, **kwargs):
            self.post_calls.append({"url": url, "json": json, "kwargs": kwargs})
            return MockResponse({"status": "error", "queued": False})

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockAsyncClient()


@pytest.fixture
def mock_user_data():
    return {"id": 1, "email": "test@example.com"}


@pytest.fixture
def mock_notification_data():
    return {
        "recipient": "test@example.com",
        "provider": "email",
        "subject": "Test Notification",
        "message": "This is a test message",
    }
