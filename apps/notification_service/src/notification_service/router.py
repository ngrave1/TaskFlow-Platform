import json
from typing import Any, Dict

import structlog
from common.models.models import NotificationDTO
from fastapi import APIRouter, BackgroundTasks, HTTPException

from .config import settings
from .emailProvider import EmailProvider
from .queue_utils import async_redis, push_notification

logger = structlog.getLogger(__name__)

router = APIRouter()

email_provider = EmailProvider(
    host=settings.stmp_host,
    port=587,
    username=settings.username,
    password=settings.password,
    from_email=settings.from_email,
    use_tls=False,
)

AVAILABLE_PROVIDERS = {
    "email": email_provider,
}


async def send_notification_task(notification_data: Dict[str, Any]):
    try:
        notification = NotificationDTO(**notification_data)

        logger.info(
            "notification.send.started",
            provider=notification.provider,
            recipient=notification.recipient,
        )

        provider = AVAILABLE_PROVIDERS.get(notification.provider)

        if not provider:
            error_msg = f"Provider '{notification.provider}' not found"
            logger.error("notification.send.failed", error=error_msg)
            await push_notification(async_redis, json.dumps(notification.model_dump()))
            return

        result = await provider.send(
            recipient=notification.recipient,
            subject=notification.subject,
            message=notification.message,
        )

        if result.success:
            logger.info(
                "notification.send.success",
                provider=notification.provider,
                message_id=result.message_id,
            )
        else:
            logger.error(
                "notification.send.failed",
                provider=notification.provider,
                error=result.error,
            )
            await push_notification(async_redis, json.dumps(notification.model_dump()))

    except Exception as e:
        logger.exception(
            "notification.send.error", error=str(e), notification_data=notification_data
        )
        await push_notification(async_redis, json.dumps(notification_data))


@router.get("/health")
async def health_check():
    redis_ok = False
    try:
        await async_redis.ping()
        redis_ok = True
    except Exception:
        pass

    providers_status = {}
    for provider_name, provider in AVAILABLE_PROVIDERS.items():
        try:
            is_valid = await provider.validate_config()
            providers_status[provider_name] = "healthy" if is_valid else "unhealthy"
        except Exception:
            providers_status[provider_name] = "unhealthy"

    return {
        "status": "healthy",
        "service": "notification-service",
        "environment": "development",
        "checks": {
            "redis": "healthy" if redis_ok else "unhealthy",
            "providers": providers_status,
        },
    }


@router.get("/providers")
async def list_providers():
    providers = []
    for provider_name, provider in AVAILABLE_PROVIDERS.items():
        is_valid = await provider.validate_config()
        providers.append(
            {
                "name": provider_name,
                "type": provider.provider_type,
                "configured": is_valid,
            }
        )

    return {"providers": providers}


@router.post("/send_notification/")
async def send_notification(
    notification: NotificationDTO,
    bg_tasks: BackgroundTasks,
):
    try:
        if notification.provider not in AVAILABLE_PROVIDERS:
            available_providers = list(AVAILABLE_PROVIDERS.keys())
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Provider '{notification.provider}' not supported. "
                    f"Available providers: {available_providers}"
                ),
            )

        provider = AVAILABLE_PROVIDERS[notification.provider]
        is_configured = await provider.validate_config()

        if not is_configured:
            logger.warning("provider.not_configured", provider=notification.provider)

        notification_dict = notification.model_dump()
        bg_tasks.add_task(send_notification_task, notification_dict)

        logger.info("notification.queued", provider=notification.provider)

        return {
            "status": "queued",
            "message": f"Notification will be sent {notification.provider}",
            "provider": notification.provider,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("notification.queue.failed", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to queue notification: {str(e)}"
        ) from e


@router.get("/notifications/queue/status")
async def get_queue_status():
    try:
        queue_length = await async_redis.llen("notifications")
        return {"queue_length": queue_length, "status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}") from e
