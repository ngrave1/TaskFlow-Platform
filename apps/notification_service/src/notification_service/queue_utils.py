from redis.asyncio import Redis

from .config import settings

async_redis = Redis(
    host=settings.redis_host, 
    port=settings.redis_port, 
    password=settings.redis_password, 
    db=settings.redis_db, 
    decode_responses=True
)


async def push_notification(
    redis_client: Redis,
    message: dict,
):
    try:
        await redis_client.rpush("notifications", message)
        return True
    except:
        raise


async def get_notification(redis_client: Redis):
    try:
        message = await redis_client.lpop("notifications")
        return message
    except:
        raise
