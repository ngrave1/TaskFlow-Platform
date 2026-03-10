from redis import Redis
from .queue_utils import get_notification
import asyncio


class worker:
    def _init_(self, redis_client: Redis, state: bool = True):
        self.redis_client = redis_client
        self.state = state

    async def process(self, func):
        while self.state:
            message = await get_notification(redis_client=self.redis_client)
            if message:
                await func()
            else:
                await asyncio.sleep(1)

    async def stop(self):
        self.state = False
