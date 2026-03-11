from fastapi import APIRouter, HTTPException

from .dependecies import SessionDep
from .help_func import (
    get_inf_about_author_helper,
    send_assing_notification,
    set_author_helper,
)
from .orm_utils import create_task_orm
from .task_schemes import TaskCreateSchema

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "task-service",
        "environment": "development",
    }


@router.post("/create_task/")
async def create_task(
    session: SessionDep,
    task: TaskCreateSchema,
):
    try:
        created_task = await create_task_orm(
            session=session,
            title=task.title,
            content=task.content,
            author_id=task.author_id,
        )

        if task.author_id:
            try:
                await send_assing_notification(
                    session=session,
                    provider="email",
                    task_id=created_task.id,
                    author_id=None,
                )
            except Exception:
                raise

        return {"message": f"Task created: {task.title}", "task_id": created_task.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}") from e


@router.post("/assing_a_worker/")
async def set_author(
    session: SessionDep,
    task_id: int,
    author_id: int,
):
    try:
        updated_task = await set_author_helper(
            session=session, task_id=task_id, author_id=author_id
        )

        if updated_task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"message": "Author assigned successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding author: {str(e)}") from e


@router.get("/get_task_by_id/")
async def get_inf_about_author_by_task_id(
    session: SessionDep,
    task_id: int,
):
    try:
        author_info = await get_inf_about_author_helper(
            session=session, task_id=task_id, author_id=None
        )

        if author_info is None:
            raise HTTPException(status_code=404, detail="No author found for this task")

        return author_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting author info: {str(e)}") from e
