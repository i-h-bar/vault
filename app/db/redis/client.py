from typing import Self

from redis.asyncio import Redis as AsyncRedis


class Redis:
    cache: Self | None = None

    def __new__(cls: type[Self]) -> Self:
        if not cls.cache:
            cls.cache = super().__new__(cls)

        return cls.cache

    def __init__(self: Self) -> None:
        self.redis = AsyncRedis()

    async def set(self: Self, key: str, value: str, ex: int = 1800) -> None:
        await self.redis.set(key, value, ex=ex)

    async def get(self: Self, key: str) -> str | None:
        if value := await self.redis.get(key):
            return value.decode()

        return None
