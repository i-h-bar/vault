from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import bcrypt
import pytest
from db.psql.users.queries import ADD_USER
from fastapi import HTTPException
from models.new.inbound import NewIn
from models.new.outbound import NewOut
from pytest import mark
from pytest_asyncio import fixture

MOCK_GET_ENV = bcrypt.gensalt()
with patch("os.getenv", return_value=MOCK_GET_ENV.decode()):
    from routes.new.new_user import create_user


def raise_error(*_: str) -> None:
    raise asyncpg.PostgresError()


@fixture
def new_user() -> NewIn:
    return NewIn(username="test", password="password")  # noqa: S106


@patch("uuid.uuid4", return_value="uuid")
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.execute", new_callable=AsyncMock)
@mark.asyncio
async def test_new_user(execute_mock: AsyncMock, _: MagicMock, uuid_mock: MagicMock, new_user: NewIn) -> None:
    user_out = await create_user(new_user)
    execute_mock.assert_called_once_with(
        ADD_USER, uuid_mock.return_value, new_user.username, bcrypt.hashpw(new_user.password.encode(), MOCK_GET_ENV)
    )

    assert isinstance(user_out, NewOut)
    assert user_out.username == new_user.username


@patch("uuid.uuid4", return_value="uuid")
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.execute", side_effect=raise_error)
@mark.asyncio
async def test_new_user_raise_error(
    execute_mock: AsyncMock, _: MagicMock, uuid_mock: MagicMock, new_user: NewIn
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await create_user(new_user)

    assert error_info.value.status_code == 500
    assert error_info.value.detail == "Internal Server Error"
    execute_mock.assert_called_once_with(
        ADD_USER, uuid_mock.return_value, new_user.username, bcrypt.hashpw(new_user.password.encode(), MOCK_GET_ENV)
    )
