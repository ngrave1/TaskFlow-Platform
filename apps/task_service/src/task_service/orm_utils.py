from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings
from .task_models import Tasks

settings = get_settings()

database_url = settings.database_url

pool_size = settings.pool_size
max_overflow = settings.max_overflow
pool_class = settings.pool_class
echo = settings.echo

engine_kwargs = {
    "url": database_url,
    "echo": echo,
}

if pool_class == NullPool:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = pool_size
    engine_kwargs["max_overflow"] = max_overflow

engine = create_async_engine(**engine_kwargs)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session():
    async with async_session_factory() as session:
        yield session


async def create_task_orm(
    session: AsyncSession,
    content: str,
    title: str,
    author_id: int | None = None,
) -> Tasks:
    if author_id:
        new_task = Tasks(title=title, content=content, author_id=author_id, status="in progress")
    else:
        new_task = Tasks(title=title, content=content, author_id=None, status="created")
    try:
        session.add(new_task)
        await session.flush()
        await session.refresh(new_task)
        return new_task
    except Exception as e:
        await session.rollback()
        raise e


async def set_author(
    session: AsyncSession,
    task_id: int,
    author_id: int,
) -> Tasks | None:
    result = await session.execute(select(Tasks).where(Tasks.id == task_id))
    task = result.scalar_one_or_none()
    if task:
        task.author_id = author_id
        task.status = "in progress"
        await session.commit()
        await session.refresh(task)
    return task


async def check_author(
    session: AsyncSession,
    task_id: int,
):
    result = await session.execute(select(Tasks.author_id).where(Tasks.id == task_id))
    author_id = result.scalar_one_or_none()
    return author_id
