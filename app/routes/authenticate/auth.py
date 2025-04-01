import json
import os

import bcrypt
import jwt
from asyncpg import Pool
from db.users.queries import GET_USER
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from lwe import Secret
from models.authenticate.token import Token
from redis.asyncio import Redis

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")


async def authenticate_user(form_data: OAuth2PasswordRequestForm, public_key: str, pool: Pool, redis: Redis) -> Token:
    user = await pool.fetchrow(GET_USER, form_data.username)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not bcrypt.checkpw(form_data.password.encode(), user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_id = str(user["id"])
    app_secret = Secret()
    app_public_key = app_secret.generate_public_key().to_b64()

    redis_keys = {
        "secret": app_secret.to_b64(),
        "public": public_key,
    }

    await redis.set(user_id, json.dumps(redis_keys), ex=1800)

    raw_token = {
        "id": user_id,
        "public_key": app_public_key,
    }

    token = jwt.encode(raw_token, JWT_SECRET)

    return Token(token=token)
