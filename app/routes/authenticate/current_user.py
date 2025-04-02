from datetime import datetime

import jwt
import pytz
from asyncpg import Pool
from db.users.queries import GET_USER_FROM_ID
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from lwe import Public, Secret
from models.user import User
from redis.asyncio import Redis

from routes.authenticate.constants import JWT_ALGORITHM, JWT_SECRET

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authenticate")


async def get_current_user(pool: Pool, redis: Redis, token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if user_id := payload.get("id"):
        expiry = datetime.fromisoformat(await redis.get(f"{user_id}-expiry"))
        if expiry > datetime.now(tz=pytz.utc):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        secret = Secret.from_b64(await redis.get(f"{user_id}-secret"))
        public = Public.from_b64(await redis.get(f"{user_id}-public"))
        user = await pool.fetchrow(GET_USER_FROM_ID, user_id)
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return User(id=user["id"], name=user["name"], public=public, secret=secret)
