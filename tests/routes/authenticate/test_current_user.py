import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, call, patch

import jwt
import pytz
from db.psql.users.queries import GET_USER_FROM_ID
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


def redis_get_mock_func(key: str) -> str | None:
    return REDIS_GETS.get(key)


@fixture
def token() -> str:
    raw_token = {
        "id": USER_ID,
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
