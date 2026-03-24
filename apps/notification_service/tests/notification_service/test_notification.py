from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_send_notification_success(test_client, notification_dto):
    with patch("src.notification_service.router.async_redis") as mock_redis:
        mock_redis.rpush = AsyncMock()

        response = test_client.post("/send_notification/", json=notification_dto.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["queued"] is True
        assert data["provider"] == "email"
        assert "Notification will be sent" in data["message"]


@pytest.mark.asyncio
async def test_send_notification_provider_not_found(test_client, notification_dto):
    notification_dto.provider = "sms"

    response = test_client.post("/send_notification/", json=notification_dto.model_dump())

    assert response.status_code == 400
    data = response.json()
    assert "Provider 'sms' not supported" in data["detail"]


@pytest.mark.asyncio
async def test_send_notification_validation_error(test_client):
    response = test_client.post("/send_notification/", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_send_notification_task_success(mock_email_provider, notification_dto):
    from src.notification_service.router import send_notification_task

    mock_email_provider.send = AsyncMock(return_value=MagicMock(success=True, message_id="test_id"))

    with (
        patch(
            "src.notification_service.router.AVAILABLE_PROVIDERS", {"email": mock_email_provider}
        ),
        patch("src.notification_service.router.push_notification") as mock_push,
    ):
        await send_notification_task(notification_dto.model_dump())

        mock_email_provider.send.assert_called_once_with(
            recipient=notification_dto.recipient,
            subject=notification_dto.subject,
            message=notification_dto.message,
        )
        mock_push.assert_not_called()


@pytest.mark.asyncio
async def test_send_notification_task_failure(mock_email_provider, notification_dto):
    from src.notification_service.router import send_notification_task

    mock_email_provider.send = AsyncMock(return_value=MagicMock(success=False, error="Send failed"))

    with (
        patch(
            "src.notification_service.router.AVAILABLE_PROVIDERS", {"email": mock_email_provider}
        ),
        patch("src.notification_service.router.push_notification") as mock_push,
    ):
        await send_notification_task(notification_dto.model_dump())

        mock_push.assert_called_once()


@pytest.mark.asyncio
async def test_send_notification_task_provider_not_found(notification_dto):
    from src.notification_service.router import send_notification_task

    with (
        patch("src.notification_service.router.AVAILABLE_PROVIDERS", {}),
        patch("src.notification_service.router.push_notification") as mock_push,
    ):
        await send_notification_task(notification_dto.model_dump())

        mock_push.assert_called_once()


@pytest.mark.asyncio
async def test_send_notification_task_exception(notification_dto):
    from src.notification_service.router import send_notification_task

    with (
        patch("src.notification_service.router.AVAILABLE_PROVIDERS", {"email": None}),
        patch("src.notification_service.router.push_notification") as mock_push,
    ):
        await send_notification_task(notification_dto.model_dump())

        mock_push.assert_called_once()
