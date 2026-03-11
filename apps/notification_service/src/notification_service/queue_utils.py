from redis.asyncio import Redis

async_redis = Redis(host="redis", port=6379, password="redis123", db=0, decode_responses=True)


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
