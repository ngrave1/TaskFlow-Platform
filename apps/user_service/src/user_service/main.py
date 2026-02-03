from fastapi import FastAPI
from .router import router
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from .user_models import Base
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(
        url=str(settings.database.url),
        echo=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(router)