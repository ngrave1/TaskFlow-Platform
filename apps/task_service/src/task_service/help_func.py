import os

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from .orm_utils import check_author, set_author

logger = structlog.getLogger(__name__)


async def get_api_gateway_url() -> str:
    if os.getenv("TESTING") == "true":
        return "http://test-api-gateway:8000"
    from common.config import get_common_settings
    common = get_common_settings()
    return common.urls.api_gateway


async def get_inf_about_author_helper(
    session: AsyncSession,
    task_id: int | None = None,
    author_id: int | None = None,
) -> dict | None:
    target_author_id = None

    if author_id is not None:
        target_author_id = author_id
    elif task_id is not None:
        target_author_id = await check_author(session=session, task_id=task_id)
    else:
        raise ValueError("Either task_id or author_id must be provided")

    if target_author_id is not None:
        api_gateway_url = await get_api_gateway_url()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_gateway_url}/tasks/with_authors/{target_author_id}"
            )
            response.raise_for_status()
            return response.json()

    return None


async def set_author_helper(
    session: AsyncSession,
    task_id: int,
    author_id: int,
):
    try:
        updated_task = await set_author(session=session, task_id=task_id, author_id=author_id)

        if not updated_task:
            return None

        await send_assign_notification(
            session=session,
            provider="email",
            task_id=task_id,
            author_id=None,
        )

        return updated_task

    except Exception as e:
        raise e


async def send_assign_notification(
    session: AsyncSession,
    provider: str,
    task_id: str | None = None,
    author_id: str | None = None,
):
    subject = "Assign a worker"
    message = "Assign a worker"
    try:
        recipient = await get_inf_about_author_helper(
            session=session, task_id=task_id, author_id=author_id
        )
    except:
        raise
    if recipient:
        logger.info(
            "help_func.send_assign_notification.response",
            recipient_email=recipient.get("email")
        )
        recipient_email = recipient.get("email")
    else:
        recipient_email = None

    api_gateway_url = await get_api_gateway_url()

    return await httpx.AsyncClient().post(
        f"{api_gateway_url}/tasks/send_notification/",
        json={
            "recipient": recipient_email,
            "provider": provider,
            "subject": subject,
            "message": message,
        },
    )