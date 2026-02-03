from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from .password_utils import hash_password
from sqlalchemy import select, delete
from .user_models import Users
from .config import settings


database_url = str(settings.database.url)  


engine = create_async_engine(
    url=database_url,
    echo=True,
    pool_size=5,
    max_overflow=10,
)


async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_session():
    async with async_session_factory() as session:
        yield session


async def get_user_by_email(
    session: AsyncSession,
    email: str,
):
    result = await session.execute(
        select(Users).where(Users.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
):
    result = await session.execute(
        select(Users).where(Users.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    email: str,
    password: str,
):
    hashed = hash_password(password)
    return Users(email=email, password=hashed)


async def session_add(session: AsyncSession, new_object):
    try:
        session.add(new_object)
        await session.commit()
    except:
        await session.rollback()
        raise


async def delete_user_orm(
    session: AsyncSession,
    user_id: int,
):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise
    await session.execute(delete(Users).where(Users.id == user_id))
    await session.commit()