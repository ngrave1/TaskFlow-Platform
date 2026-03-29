import json

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .config import settings

async_redis = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_db,
    decode_responses=True,
)


logger = structlog.get_logger(__name__)


async def push_notification(redis_client, notification_data: dict):
    try:
        if isinstance(notification_data, dict):
            data = json.dumps(notification_data)
        else:
            data = notification_data

        result = await redis_client.rpush("notifications", data)
        logger.debug("notification.pushed", queue_length=result)
        return True
    except RedisError as e:
        logger.error("redis.push.failed", error=str(e))
        raise
    except Exception as e:
        logger.error("push.failed", error=str(e))
        raise


async def get_notification(redis_client):
    try:
        notification = await redis_client.lpop("notifications")
        if notification:
            logger.debug("notification.received")
        return notification
    except RedisError as e:
        logger.error("redis.pop.failed", error=str(e))
        raise
    except Exception as e:
        logger.error("pop.failed", error=str(e))
        raise
