import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, call, patch

import bcrypt
import jwt
import pytest
import pytz
from db.psql.users.queries import GET_USER
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from freezegun import freeze_time
from lwe import Public, Secret
from models.authenticate.output import Token
from pytest import fixture, mark
from starlette.datastructures import Headers

FAKE_SECRET = "JWT_SECRET"  # noqa: S105
with patch("os.getenv", return_value=FAKE_SECRET):
    from routes.authenticate.auth import authenticate_user
    from routes.authenticate.constants import JWT_ALGORITHM, SESSION_DURATION

TEST_TIME = datetime.now(tz=pytz.UTC)
SECRET = Secret()
PUBLIC = SECRET.generate_public_key()
PASSWORD = "password"  # noqa: S105
USER_FETCH = {
    "id": uuid.uuid4(),
    "name": "test",
    "hashed_password": bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()),
}


@fixture
def form_data() -> OAuth2PasswordRequestForm:
    return OAuth2PasswordRequestForm(
        username="test",
        password=PASSWORD,
        client_secret=PUBLIC.to_b64(),
    )


@fixture
def form_data_bad_pub_key() -> OAuth2PasswordRequestForm:
    return OAuth2PasswordRequestForm(
        username="test",
        password=PASSWORD,
        client_secret="asdasdasda",  # noqa: S106
    )


@fixture
def form_data_wrong_password() -> OAuth2PasswordRequestForm:
    return OAuth2PasswordRequestForm(
        username="test",
        password="Wrong Password",  # noqa: S106
        client_secret=PUBLIC.to_b64(),
    )


@fixture
def form_data_no_client_secret() -> OAuth2PasswordRequestForm:
    return OAuth2PasswordRequestForm(
        username="test",
        password=PASSWORD,
    )


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


@patch("lwe.Secret.to_b64", return_value="secret_b64")
@patch("db.redis.client.Redis", new_callable=MagicMock)
@patch("db.redis.client.Redis.set", new_callable=AsyncMock)
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_auth_positive_flow(
    row_mock: AsyncMock,
    _: MagicMock,
    set_mock: AsyncMock,
    __: MagicMock,
    secret_b64_mock: MagicMock,
    form_data: OAuth2PasswordRequestForm,
    request_obj: Request,
) -> None:
    token = await authenticate_user(form_data, request_obj)
    row_mock.assert_called_once_with(GET_USER, form_data.username)
    assert set_mock.call_count == 4
    expiry = (TEST_TIME + timedelta(seconds=SESSION_DURATION)).isoformat()
    set_mock.assert_has_calls(
        [
            call(f"{row_mock.return_value['id']!s}-secret", secret_b64_mock.return_value, ex=SESSION_DURATION),
            call(f"{row_mock.return_value['id']!s}-public", form_data.client_secret, ex=SESSION_DURATION),
            call(f"{row_mock.return_value['id']!s}-expiry", expiry, ex=SESSION_DURATION),
            call(f"{row_mock.return_value['id']!s}-ip", request_obj.client.host, ex=SESSION_DURATION),
        ],
        any_order=True,
    )

    assert isinstance(token, Token)
    jwt_token = jwt.decode(token.access_token, FAKE_SECRET, algorithms=JWT_ALGORITHM)
    assert jwt_token["expires"] == expiry
    assert jwt_token["id"] == str(row_mock.return_value["id"])
    assert jwt_token["duration"] == SESSION_DURATION

    assert token.token_type == "Bearer"  # noqa: S105

    Public.from_b64(token.public_key)


@patch("db.redis.client.Redis", new_callable=MagicMock)
@patch("db.redis.client.Redis.set", new_callable=AsyncMock)
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_auth_no_client_secret(
    row_mock: AsyncMock,
    _: MagicMock,
    set_mock: AsyncMock,
    __: MagicMock,
    form_data_no_client_secret: OAuth2PasswordRequestForm,
    request_obj: Request,
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await authenticate_user(form_data_no_client_secret, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid client secret"

    row_mock.assert_not_called()
    set_mock.assert_not_called()


@patch("db.redis.client.Redis", new_callable=MagicMock)
@patch("db.redis.client.Redis.set", new_callable=AsyncMock)
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=None)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_auth_no_user(
    row_mock: AsyncMock,
    _: MagicMock,
    set_mock: AsyncMock,
    __: MagicMock,
    form_data: OAuth2PasswordRequestForm,
    request_obj: Request,
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await authenticate_user(form_data, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid username or password"

    row_mock.assert_called_once_with(GET_USER, form_data.username)
    set_mock.assert_not_called()


@patch("db.redis.client.Redis", new_callable=MagicMock)
@patch("db.redis.client.Redis.set", new_callable=AsyncMock)
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_auth_wrong_password(
    row_mock: AsyncMock,
    _: MagicMock,
    set_mock: AsyncMock,
    __: MagicMock,
    form_data_wrong_password: OAuth2PasswordRequestForm,
    request_obj: Request,
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await authenticate_user(form_data_wrong_password, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid username or password"

    row_mock.assert_called_once_with(GET_USER, form_data_wrong_password.username)
    set_mock.assert_not_called()


@patch("starlette.requests.Request.client", new_callable=lambda: PropertyMock(return_value=None))
@patch("db.redis.client.Redis", new_callable=MagicMock)
@patch("db.redis.client.Redis.set", new_callable=AsyncMock)
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_auth_no_client(
    row_mock: AsyncMock,
    _: MagicMock,
    set_mock: AsyncMock,
    __: MagicMock,
    ___: MagicMock,
    form_data: OAuth2PasswordRequestForm,
    request_obj: Request,
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await authenticate_user(form_data, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid client"

    row_mock.assert_not_called()
    set_mock.assert_not_called()


@patch("db.redis.client.Redis", new_callable=MagicMock)
@patch("db.redis.client.Redis.set", new_callable=AsyncMock)
@patch("db.psql.client.Psql", new_callable=MagicMock)
@patch("db.psql.client.Psql.fetch_row", new_callable=AsyncMock, return_value=USER_FETCH)
@freeze_time(TEST_TIME.isoformat())
@mark.asyncio
async def test_auth_invalid_public_key(
    row_mock: AsyncMock,
    _: MagicMock,
    set_mock: AsyncMock,
    __: MagicMock,
    form_data_bad_pub_key: OAuth2PasswordRequestForm,
    request_obj: Request,
) -> None:
    with pytest.raises(HTTPException) as error_info:
        await authenticate_user(form_data_bad_pub_key, request_obj)

    assert error_info.value.status_code == 401
    assert error_info.value.detail == "Invalid client secret"

    row_mock.assert_not_called()
    set_mock.assert_not_called()
