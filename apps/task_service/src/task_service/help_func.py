import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .orm_utils import check_author, set_author


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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.api_gateway_url}/tasks/with_autors/{target_author_id}"
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

        await send_assing_notification(
            session=session,
            provider="email",
            task_id=task_id,
            author_id=None,
        )

        return updated_task

    except Exception as e:
        raise e


async def send_assing_notification(
    session: AsyncSession,
    provider: str,
    task_id: str | None = None,
    author_id: str | None = None,
):
    subject = "Assing a worker"
    message = "Assing a worker"
    try:
        recipient = await get_inf_about_author_helper(
            session=session, task_id=task_id, author_id=author_id
        )
    except:
        raise
    return await httpx.AsyncClient().post(
        f"{settings.api_gateway_url}/tasks/with_autors/",
        json={
            "recipient": recipient,
            "provider": provider,
            "subject": subject,
            "message": message,
        },
    )
