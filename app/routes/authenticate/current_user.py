from datetime import datetime

import jwt
import pytz
from asyncpg import Pool
from db.psql.users.queries import GET_USER_FROM_ID
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from lwe import Public, Secret
from models.user import User
from redis.asyncio import Redis

from routes.authenticate.constants import JWT_ALGORITHM, JWT_SECRET

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authenticate")


async def get_current_user(pool: Pool, redis: Redis, request: Request, token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not (client := request.client):
        raise HTTPException(status_code=401, detail="Invalid client")

    if not (user_id := payload.get("id")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expiry = datetime.fromisoformat(await redis.get(f"{user_id}-expiry"))
    if expiry > datetime.now(tz=pytz.utc):
        raise HTTPException(status_code=401, detail="Token has expired")

    ip = await redis.get(f"{user_id}-ip")
    if ip != client.host:
        raise HTTPException(status_code=401, detail="Invalid ip please reauthenticate")

    secret = Secret.from_b64(await redis.get(f"{user_id}-secret"))
    public = Public.from_b64(await redis.get(f"{user_id}-public"))
    user = await pool.fetchrow(GET_USER_FROM_ID, user_id)

    return User(id=user["id"], name=user["name"], public=public, secret=secret)
