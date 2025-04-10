import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, call, patch

import jwt
import pytest
import pytz
from db.psql.users.queries import GET_USER_FROM_ID
from fastapi import HTTPException
from freezegun import freeze_time
from lwe import Public, Secret
from models.user import User
from pytest import mark
from pytest_asyncio import fixture
from starlette.datastructures import Headers
from starlette.requests import Request

FAKE_SECRET = "JWT_SECRET"  # noqa: S105
with patch("os.getenv", return_value=FAKE_SECRET):
    from routes.authenticate.constants import SESSION_DURATION
    from routes.authenticate.current_user import get_current_user

TEST_TIME = datetime.now(tz=pytz.UTC)
USER_ID = str(uuid.uuid4())
SECRET = Secret()
PUBLIC = SECRET.generate_public_key()
USER_FETCH = {"id": USER_ID, "name": "test"}
REDIS_GETS = {
    f"{USER_ID}-ip": "127.0.0.1",
    f"{USER_ID}-expiry": (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat(),
    f"{USER_ID}-public": PUBLIC.to_b64(),
    f"{USER_ID}-secret": SECRET.to_b64(),
}
REDIS_GETS_NO_IP = {
    f"{USER_ID}-expiry": (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat(),
    f"{USER_ID}-public": PUBLIC.to_b64(),
    f"{USER_ID}-secret": SECRET.to_b64(),
}
REDIS_GETS_WRONG_IP = {
    f"{USER_ID}-ip": "128.1.1.1",
    f"{USER_ID}-expiry": (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat(),
    f"{USER_ID}-public": PUBLIC.to_b64(),
    f"{USER_ID}-secret": SECRET.to_b64(),
}
REDIS_GETS_NO_SECRET = {
    f"{USER_ID}-ip": "127.0.0.1",
    f"{USER_ID}-expiry": (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat(),
    f"{USER_ID}-public": PUBLIC.to_b64(),
}
REDIS_GETS_NO_PUBLIC = {
    f"{USER_ID}-ip": "127.0.0.1",
    f"{USER_ID}-expiry": (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat(),
    f"{USER_ID}-secret": SECRET.to_b64(),
}


def redis_get_mock_func(key: str) -> str | None:
    return REDIS_GETS.get(key)


def redis_get_mock_func_no_ip(key: str) -> str | None:
    return REDIS_GETS_NO_IP.get(key)


def redis_get_mock_func_wrong_ip(key: str) -> str | None:
    return REDIS_GETS_WRONG_IP.get(key)


def redis_get_mock_func_no_secret(key: str) -> str | None:
    return REDIS_GETS_NO_SECRET.get(key)


def redis_get_mock_func_no_public(key: str) -> str | None:
    return REDIS_GETS_NO_PUBLIC.get(key)


@fixture
def token() -> str:
    raw_token = {
        "id": USER_ID,
        "expires": (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat(),
        "duration": SESSION_DURATION,
    }
    return jwt.encode(raw_token, FAKE_SECRET)


@fixture
def token_no_id() -> str:
    raw_token = {
        "expires": (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat(),
        "duration": SESSION_DURATION,
    }
    return jwt.encode(raw_token, FAKE_SECRET)


@fixture
def request_obj() -> Request:
    return Request(
        {
            "type": "http",
            "path": "/authenticate",
            "headers": Headers({"Content-Type": "application/x-www-form-urlencoded"}).raw,
            "http_version": "1.1",
            "method": "GET",
            "scheme": "https",
            "client": ("127.0.0.1", 8080),
            "server": ("www.example.com", 443),
        }
    )


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_get_current_user_positive(
    get_mock: AsyncMock, row_mock: AsyncMock, token: str, request_obj: Request
) -> None:
    user = await get_current_user(token, request_obj)

    assert isinstance(user, User)
    assert user.id == USER_ID
    assert user.name == USER_FETCH["name"]
    assert isinstance(user.public, Public)
    assert isinstance(user.secret, Secret)
    assert user.secret.to_b64() == SECRET.to_b64()
    assert user.public.to_b64() == PUBLIC.to_b64()

    row_mock.assert_called_once_with(GET_USER_FROM_ID, USER_ID)
    assert get_mock.call_count == 4
    get_mock.assert_has_calls([call(key) for key in REDIS_GETS], any_order=True)


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func)
@mark.asyncio
async def test_get_current_user_invalid_jwt(get_mock: AsyncMock, row_mock: AsyncMock, request_obj: Request) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user("Invalid", request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid username or password"
    row_mock.assert_not_called()
    get_mock.assert_not_called()


@patch("starlette.requests.Request.client", new_callable=lambda: PropertyMock(return_value=None))
@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func)
@mark.asyncio
async def test_get_current_user_no_client(
    get_mock: AsyncMock, row_mock: AsyncMock, _: MagicMock, token: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid client"
    row_mock.assert_not_called()
    get_mock.assert_not_called()


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", new_callable=AsyncMock, return_value=None)
@mark.asyncio
async def test_get_current_user_no_expiry(
    get_mock: AsyncMock, row_mock: AsyncMock, token: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid username or password"
    row_mock.assert_not_called()
    get_mock.assert_called_once_with(f"{USER_FETCH['id']}-expiry")


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", new_callable=AsyncMock, return_value=TEST_TIME.isoformat())
@freeze_time((TEST_TIME + timedelta(seconds=1)).isoformat())
@mark.asyncio
async def test_get_current_user_expired_token(
    get_mock: AsyncMock, row_mock: AsyncMock, token: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Token has expired"
    row_mock.assert_not_called()
    get_mock.assert_called_once_with(f"{USER_FETCH['id']}-expiry")


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func_no_ip)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_get_current_user_no_ip(
    get_mock: AsyncMock, row_mock: AsyncMock, token: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid ip please reauthenticate"
    row_mock.assert_not_called()
    assert get_mock.call_count == 2
    get_mock.assert_has_calls([call(f"{USER_FETCH['id']}-expiry"), call(f"{USER_FETCH['id']}-ip")])


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func_wrong_ip)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_get_current_user_wrong_ip(
    get_mock: AsyncMock, row_mock: AsyncMock, token: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid ip please reauthenticate"
    row_mock.assert_not_called()
    assert get_mock.call_count == 2
    get_mock.assert_has_calls([call(f"{USER_FETCH['id']}-expiry"), call(f"{USER_FETCH['id']}-ip")])


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func_no_secret)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_get_current_user_no_secret(
    get_mock: AsyncMock, row_mock: AsyncMock, token: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid username or password"
    row_mock.assert_not_called()
    assert get_mock.call_count == 4
    get_mock.assert_has_calls([call(key) for key in REDIS_GETS], any_order=True)


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func_no_public)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_get_current_user_no_public(
    get_mock: AsyncMock, row_mock: AsyncMock, token: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid username or password"
    row_mock.assert_not_called()
    assert get_mock.call_count == 4
    get_mock.assert_has_calls([call(key) for key in REDIS_GETS], any_order=True)


@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@patch("db.redis.client.Redis.get", side_effect=redis_get_mock_func)
@mark.asyncio
async def test_get_current_user_no_user_id(
    get_mock: AsyncMock, row_mock: AsyncMock, token_no_id: str, request_obj: Request
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await get_current_user(token_no_id, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid username or password"
    row_mock.assert_not_called()
    get_mock.assert_not_called()
