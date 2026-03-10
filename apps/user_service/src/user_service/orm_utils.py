import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from .password_utils import hash_password
from sqlalchemy import select, delete
from .user_models import Users
from .config import settings

# Определяем engine как None - будет создан при первом использовании
_engine = None
_async_session_factory = None
is_testing = os.getenv("TESTING") == "true"


def get_engine():
    """Создает engine с учетом режима тестирования."""
    global _engine
    if _engine is None:
        if is_testing:
            database_url = "sqlite+aiosqlite:///file::memory:?cache=shared"
            from sqlalchemy.pool import StaticPool

            _engine = create_async_engine(
                database_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False,
            )
        else:
            database_url = str(settings.database_url)
            _engine = create_async_engine(
                database_url,
                pool_size=5,
                max_overflow=10,
                echo=False,
            )
    return _engine


def get_session_factory():
    """Возвращает фабрику сессий."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _async_session_factory


async def get_session():
    """Генератор сессий для FastAPI зависимостей."""
    async with get_session_factory()() as session:
        yield session


async def get_user_by_email(
    session: AsyncSession,
    email: str,
):
    result = await session.execute(select(Users).where(Users.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
):
    result = await session.execute(select(Users).where(Users.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    email: str,
    password: str,
):
    hashed = hash_password(password)
    return Users(email=email, password=hashed)


async def delete_user_orm(
    session: AsyncSession,
    user_id: int,
):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"User with id {user_id} not found")
    await session.execute(delete(Users).where(Users.id == user_id))
    await session.commit()
