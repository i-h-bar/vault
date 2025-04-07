from unittest.mock import AsyncMock, patch

from db.redis.client import Redis
from pytest import fixture, mark
from redis.asyncio import Redis as AsyncRedis


@fixture
def redis() -> Redis:
    return Redis()


def test_redis_cache() -> None:
    assert Redis.cache is None
    db = Redis()
    assert Redis.cache is not None
    assert id(Redis.cache) == id(db)
    assert Redis.cache is db

    db_2 = Redis()
    assert id(db) == id(db_2)
    assert db is db_2
    assert isinstance(Redis.cache.redis, AsyncRedis)


@patch("redis.asyncio.Redis.set", new_callable=AsyncMock)
@mark.asyncio
async def test_redis_set(set_mock: AsyncMock, redis: Redis) -> None:
    await redis.set("key", "value")
    set_mock.assert_called_once_with("key", "value", ex=1800)


@patch("redis.asyncio.Redis.get", new_callable=AsyncMock, return_value=b"value")
@mark.asyncio
async def test_redis_get(get_mock: AsyncMock, redis: Redis) -> None:
    value = await redis.get("key")
    get_mock.assert_called_once_with("key")
    assert value == get_mock.return_value.decode()


@patch("redis.asyncio.Redis.get", new_callable=AsyncMock, return_value=None)
@mark.asyncio
async def test_redis_get_none(get_mock: AsyncMock, redis: Redis) -> None:
    value = await redis.get("key")
    get_mock.assert_called_once_with("key")
    assert value is None
