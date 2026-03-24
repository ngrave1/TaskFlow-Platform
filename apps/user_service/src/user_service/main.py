from contextlib import asynccontextmanager

import structlog
from common.logger_config import setup_logging
from fastapi import FastAPI

from .router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(
        environment="development",
        debug=True,
    )
    logger = structlog.get_logger("user-service")
    logger.info("user-service.starting")
    yield
    logger.info("user-service.shutting_down")


app = FastAPI(lifespan=lifespan)
app.include_router(router)
