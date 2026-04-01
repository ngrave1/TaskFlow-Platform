from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .config import get_settings
from .password_utils import hash_password
from .user_models import Users

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
