from fastapi import FastAPI
from .router import router
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from .user_models import Base
import structlog
from .config import settings

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger("user-service")

app = FastAPI()
app.include_router(router)
