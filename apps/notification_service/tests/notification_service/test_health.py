from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_health_check(test_client, mock_redis):
    with pytest.MonkeyPatch.context() as mp:
        
        mp.setattr("src.notification_service.router.async_redis", mock_redis)
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"
        assert data["environment"] == "development"
        assert "checks" in data
        assert "redis" in data["checks"]
        assert "providers" in data["checks"]


@pytest.mark.asyncio
async def test_health_check_redis_failure(test_client, mock_redis):
    mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
    
    with pytest.MonkeyPatch.context() as mp:
        
        mp.setattr("src.notification_service.router.async_redis", mock_redis)
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["redis"] == "unhealthy"


@pytest.mark.asyncio
async def test_health_check_provider_unhealthy(test_client, mock_redis, mock_email_provider):
    mock_email_provider.validate_config = AsyncMock(return_value=False)
    
    with pytest.MonkeyPatch.context() as mp:
        
        mp.setattr("src.notification_service.router.async_redis", mock_redis)
        mp.setattr("src.notification_service.router.AVAILABLE_PROVIDERS", 
                   {"email": mock_email_provider})
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["providers"]["email"] == "unhealthy"
