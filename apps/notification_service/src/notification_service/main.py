from contextlib import asynccontextmanager

import structlog
from common.config import common_settings
from common.logger_config import setup_logging
from fastapi import FastAPI

from .router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(
        environment=common_settings.environment,
        debug=common_settings.debug,
    )
    logger = structlog.get_logger("notification-service")
    logger.info("notification-service.starting")
    yield
    logger.info("notification-service.shutting_down")


app = FastAPI(lifespan=lifespan)
app.include_router(router)
