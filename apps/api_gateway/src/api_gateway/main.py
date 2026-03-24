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
    logger = structlog.get_logger("api-gateway")
    logger.info("api-gateway.starting")
    yield
    logger.info("api-gateway.shutting_down")


app = FastAPI(lifespan=lifespan)
app.include_router(router)