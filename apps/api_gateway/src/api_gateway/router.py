import httpx
from common.models.models import NotificationDTO, UserDtoSchema
from fastapi import APIRouter

from .config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "environment": "development",
    }


@router.get("/tasks/with_autors/{author_id}")
async def get_tasks_with_authors(author_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.USER_URL}/recive_user_by_id/{author_id}")
        if response.status_code == 200:
            user_data = response.json()
            user_dto = UserDtoSchema(**user_data)
            return user_dto
        else:
            raise


@router.post("/tasks/send_notification")
async def get_tasks_with_authors(
    recipient: int,
    provider: str,
    subject: str,
    message: str,
):
    notification_dto = NotificationDTO(
        recipient=recipient,
        provider=provider,
        subject=subject,
        message=message,
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.NOTIFICATION_URL}/send_notification/",
            json=notification_dto.model_dump(),
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "queued" or result.get("queued"):
                return True
            else:
                raise Exception(f"Failed to send notification: {result}")
        else:
            raise Exception(f"HTTP error {response.status_code}: {response.text}")
