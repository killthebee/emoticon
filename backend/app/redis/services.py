from aioredis import Redis


class Service:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def save_emoticon_word(self, emoticon_word) -> bool:
        await self._redis.set(f"{emoticon_word}", "saved")
        return True

    async def get_emoticon_word(self, emoticon_word) -> str:
        return await self._redis.get(emoticon_word, encoding="utf-8")
