from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_list_providers(test_client, mock_email_provider):
    mock_email_provider.validate_config = AsyncMock(return_value=True)

    with patch.dict(
        "src.notification_service.router.AVAILABLE_PROVIDERS", {"email": mock_email_provider}
    ):
        response = test_client.get("/providers")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) == 1
        assert data["providers"][0]["name"] == "email"
        assert data["providers"][0]["type"] == "email"
        assert data["providers"][0]["configured"] is True


@pytest.mark.asyncio
async def test_list_providers_not_configured(test_client, mock_email_provider):
    mock_email_provider.validate_config = AsyncMock(return_value=False)

    with patch.dict(
        "src.notification_service.router.AVAILABLE_PROVIDERS", {"email": mock_email_provider}
    ):
        response = test_client.get("/providers")

        assert response.status_code == 200
        data = response.json()
        assert data["providers"][0]["configured"] is False


@pytest.mark.asyncio
async def test_email_provider_send_success():
    from src.notification_service.email_provider import EmailProvider

    provider = EmailProvider(
        host="smtp.test.com",
        port=465,
        username="test@test.com",
        password="password",
        from_email="from@test.com",
        use_tls=True,
    )

    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance

        result = await provider.send(
            recipient="test@example.com", subject="Test", message="Test message"
        )

        assert result.success is True
        assert result.message_id is not None
        mock_smtp_instance.login.assert_called_once_with("test@test.com", "password")
        mock_smtp_instance.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_email_provider_send_failure():
    from src.notification_service.email_provider import EmailProvider

    provider = EmailProvider(
        host="smtp.test.com",
        port=465,
        username="test@test.com",
        password="password",
        from_email="from@test.com",
        use_tls=True,
    )

    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
        mock_smtp_instance.login.side_effect = Exception("Connection failed")

        result = await provider.send(
            recipient="test@example.com", subject="Test", message="Test message"
        )

        assert result.success is False
        assert result.error is not None


@pytest.mark.asyncio
async def test_email_provider_validate_config_success():
    from src.notification_service.email_provider import EmailProvider

    provider = EmailProvider(
        host="smtp.test.com",
        port=465,
        username="test@test.com",
        password="password",
        from_email="from@test.com",
        use_tls=True,
    )

    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_smtp_instance = AsyncMock()
        mock_smtp.return_value.__aenter__.return_value = mock_smtp_instance
        mock_smtp_instance.noop = AsyncMock()

        result = await provider.validate_config()

        assert result is True


@pytest.mark.asyncio
async def test_email_provider_validate_config_failure():
    from src.notification_service.email_provider import EmailProvider

    provider = EmailProvider(
        host="smtp.test.com",
        port=465,
        username="test@test.com",
        password="password",
        from_email="from@test.com",
        use_tls=True,
    )

    with patch("aiosmtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__aenter__.side_effect = Exception("Connection failed")

        result = await provider.validate_config()

        assert result is False
