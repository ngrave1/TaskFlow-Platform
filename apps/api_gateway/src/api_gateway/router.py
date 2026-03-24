import httpx
import structlog
from common.models.models import NotificationDTO, UserDtoSchema
from fastapi import APIRouter, HTTPException

from .config import settings

logger = structlog.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "environment": "development",
    }


@router.get("/tasks/with_authors/{author_id}")
async def get_tasks_with_authors(author_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.USER_URL}/receive_user_by_id/{author_id}")
        logger.info(
            "api_gateway.get_user.response",
            status_code=response.status_code,
            response_body=response.text[:200],
        )
        if response.status_code == 200:
            user_data = response.json()
            try:
                user_dto = UserDtoSchema(**user_data)
                logger.info("api_gateway.get_user.success", email=user_dto.email)
                return user_dto
            except Exception as e:
                logger.exception("api_gateway.get_user.validation_error", error=str(e))
                raise HTTPException(status_code=500, detail=f"Invalid user data: {e}") from e
        else:
            raise HTTPException(
                status_code=response.status_code, detail=f"User service error: {response.text}"
            )


@router.post("/tasks/send_notification/")
async def send_notification(notification: NotificationDTO):
    logger.info(
        "api_gateway.notification.received",
        recipient=notification.recipient,
        provider=notification.provider,
        subject=notification.subject,
        message_length=len(notification.message) if notification.message else 0,
    )
    try:
        logger.info("api_gateway.notification.validated", dto=notification.model_dump())

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.NOTIFICATION_URL}/send_notification/",
                json=notification.model_dump(),
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "queued" or result.get("queued"):
                    return {"status": "success", "message": "Notification queued"}
                else:
                    logger.warning("api_gateway.notification.unexpected_response", result=result)
                    return {
                        "status": "warning",
                        "message": "Notification sent but response unexpected",
                    }
            else:
                logger.error(
                    "api_gateway.notification.http_error",
                    status_code=response.status_code,
                    response=response.text,
                )
                return {"status": "success", "message": "Notification sent (despite HTTP error)"}

    except Exception as e:
        logger.exception(
            "api_gateway.notification.failed",
            error=str(e),
            recipient=notification.recipient,
            provider=notification.provider,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e
