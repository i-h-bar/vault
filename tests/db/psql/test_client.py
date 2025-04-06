from unittest.mock import AsyncMock, MagicMock, patch

from db.psql.client import Psql
from pytest import mark


def test_new_cache() -> None:
    assert Psql.cache is None
    db = Psql()
    assert Psql.cache is not None
    assert id(Psql.cache) == id(db)
    assert Psql.cache is db

    db_2 = Psql()
    assert id(db) == id(db_2)
    assert db is db_2


@patch("os.getenv", return_value="foo")
@patch("asyncpg.create_pool", new_callable=AsyncMock)
@mark.asyncio
async def test_db_context_manager(create_pool_mock: AsyncMock, os_get_env_mock: MagicMock) -> None:
    async with Psql():
        os_get_env_mock.assert_called_once_with("PSQL_URI")
        create_pool_mock.assert_called_once_with(dsn=os_get_env_mock.return_value)

    create_pool_mock.return_value.close.assert_called_once()


@patch("os.getenv", return_value="foo")
@patch("asyncpg.create_pool", new_callable=AsyncMock)
@mark.asyncio
async def test_execute(create_pool_mock: AsyncMock, _: MagicMock) -> None:
    query = "SELECT * FROM users where id = $1 and age < $2"
    arg_1 = "12345"
    arg_2 = 6
    async with Psql() as db:
        await db.execute(query, arg_1, arg_2)

    create_pool_mock.return_value.execute.assert_called_once_with(query, arg_1, arg_2)


@patch("os.getenv", return_value="foo")
@patch("asyncpg.create_pool", new_callable=AsyncMock)
@mark.asyncio
async def test_fetch_row(create_pool_mock: AsyncMock, _: MagicMock) -> None:
    query = "SELECT * FROM users where id = $1 and age < $2"
    arg_1 = "12345"
    arg_2 = 6
    async with Psql() as db:
        await db.fetch_row(query, arg_1, arg_2)

    create_pool_mock.return_value.fetchrow.assert_called_once_with(query, arg_1, arg_2)
