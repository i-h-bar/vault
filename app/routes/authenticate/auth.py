import json
from datetime import datetime, timedelta

import bcrypt
import jwt
import pytz
from asyncpg import Pool
from db.users.queries import GET_USER
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from lwe import Secret
from models.authenticate.output import AuthOut, Token
from redis.asyncio import Redis

from routes.authenticate.constants import JWT_SECRET, SESSION_DURATION


async def authenticate_user(form_data: OAuth2PasswordRequestForm, public_key: str, pool: Pool, redis: Redis) -> AuthOut:
    user = await pool.fetchrow(GET_USER, form_data.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not bcrypt.checkpw(form_data.password.encode(), user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_id = str(user["id"])
    app_secret = Secret()
    app_public_key = app_secret.generate_public_key().to_b64()

    expires = (datetime.now(tz=pytz.UTC) + timedelta(seconds=SESSION_DURATION)).isoformat()
    redis_data = {
        "secret": app_secret.to_b64(),
        "public": public_key,
        "expires": expires,
    }

    await redis.set(user_id, json.dumps(redis_data), ex=SESSION_DURATION)

    raw_token = {
        "id": user_id,
        "expires": expires,
        "duration": SESSION_DURATION,
    }

    token = Token(token=jwt.encode(raw_token, JWT_SECRET))

    return AuthOut(token=token, public_key=app_public_key)
