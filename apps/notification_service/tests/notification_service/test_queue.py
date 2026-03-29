from unittest.mock import AsyncMock, patch

import pytest
from redis.exceptions import RedisError


@pytest.mark.asyncio
async def test_get_queue_status(test_client, mock_redis):
    mock_redis.llen = AsyncMock(return_value=5)

    with patch("src.notification_service.router.async_redis", mock_redis):
        response = test_client.get("/notifications/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert data["queue_length"] == 5
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_queue_status_redis_failure(test_client, mock_redis):
    mock_redis.llen = AsyncMock(side_effect=RedisError("Redis connection failed"))

    with patch("src.notification_service.router.async_redis", mock_redis):
        response = test_client.get("/notifications/queue/status")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to get queue status" in data["detail"]


@pytest.mark.asyncio
async def test_push_notification_success():
    from src.notification_service.queue_utils import push_notification

    mock_redis = AsyncMock()
    mock_redis.rpush = AsyncMock(return_value=1)

    result = await push_notification(mock_redis, {"test": "data"})

    assert result is True
    mock_redis.rpush.assert_called_once_with("notifications", '{"test": "data"}')


@pytest.mark.asyncio
async def test_push_notification_failure():
    from src.notification_service.queue_utils import push_notification

    mock_redis = AsyncMock()
    mock_redis.rpush = AsyncMock(side_effect=RedisError("Redis error"))

    with pytest.raises(RedisError, match="Redis error"):
        await push_notification(mock_redis, {"test": "data"})


@pytest.mark.asyncio
async def test_push_notification_failure_with_custom_error():
    from src.notification_service.queue_utils import push_notification

    mock_redis = AsyncMock()
    mock_redis.rpush = AsyncMock(side_effect=RedisError("Connection timeout"))

    with pytest.raises(RedisError) as exc_info:
        await push_notification(mock_redis, {"test": "data"})

    assert "Connection timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_notification_success():
    from src.notification_service.queue_utils import get_notification

    mock_redis = AsyncMock()
    mock_redis.lpop = AsyncMock(return_value='{"test": "data"}')

    result = await get_notification(mock_redis)

    assert result == '{"test": "data"}'
    mock_redis.lpop.assert_called_once_with("notifications")


@pytest.mark.asyncio
async def test_get_notification_empty():
    from src.notification_service.queue_utils import get_notification

    mock_redis = AsyncMock()
    mock_redis.lpop = AsyncMock(return_value=None)

    result = await get_notification(mock_redis)

    assert result is None


@pytest.mark.asyncio
async def test_get_notification_failure():
    from src.notification_service.queue_utils import get_notification

    mock_redis = AsyncMock()
    mock_redis.lpop = AsyncMock(side_effect=RedisError("Redis error"))

    with pytest.raises(RedisError, match="Redis error"):
        await get_notification(mock_redis)


@pytest.mark.asyncio
async def test_get_notification_failure_with_connection_error():
    from src.notification_service.queue_utils import get_notification

    mock_redis = AsyncMock()
    mock_redis.lpop = AsyncMock(side_effect=ConnectionError("Cannot connect to Redis"))

    with pytest.raises(ConnectionError, match="Cannot connect to Redis"):
        await get_notification(mock_redis)
