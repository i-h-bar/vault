import asyncio
from datetime import datetime, timedelta

import bcrypt
import jwt
import pytz
from db.psql.client import Psql
from db.psql.users.queries import GET_USER
from db.redis.client import Redis
from fastapi import HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from lwe import Public, Secret
from models.authenticate.output import Token

from routes.authenticate.constants import JWT_SECRET, SESSION_DURATION


async def authenticate_user(form_data: OAuth2PasswordRequestForm, request: Request) -> Token:
    if not form_data.client_secret:
        raise HTTPException(status_code=401, detail="Invalid client secret")

    try:
        Public.from_b64(form_data.client_secret)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid client secret")

    if not (user := await Psql().fetch_row(GET_USER, form_data.username)):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not bcrypt.checkpw(form_data.password.encode(), user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not (client := request.client):
        raise HTTPException(status_code=401, detail="Invalid client")

    user_id = str(user["id"])
    app_secret = Secret()
    app_public_key = app_secret.generate_public_key().to_b64()

    expires = (datetime.now(tz=pytz.UTC) + timedelta(seconds=SESSION_DURATION)).isoformat()

    redis = Redis()
    await asyncio.gather(
        redis.set(f"{user_id}-secret", app_secret.to_b64(), ex=SESSION_DURATION),
        redis.set(f"{user_id}-public", form_data.client_secret, ex=SESSION_DURATION),
        redis.set(f"{user_id}-expiry", expires, ex=SESSION_DURATION),
        redis.set(f"{user_id}-ip", client.host, ex=SESSION_DURATION),
    )

    raw_token = {
        "id": user_id,
        "expires": expires,
        "duration": SESSION_DURATION,
    }

    return Token(access_token=jwt.encode(raw_token, JWT_SECRET), public_key=app_public_key)
