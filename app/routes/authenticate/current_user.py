import asyncio
from datetime import datetime

import jwt
import pytz
from db.psql.client import Psql
from db.psql.users.queries import GET_USER_FROM_ID
from db.redis.client import Redis
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from lwe import Public, Secret
from models.user import User

from routes.authenticate.constants import JWT_ALGORITHM, JWT_SECRET

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authenticate")


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not (client := request.client):
        raise HTTPException(status_code=401, detail="Invalid client")

    if not (user_id := payload.get("id")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    redis = Redis()

    if not (raw_date := await redis.get(f"{user_id}-expiry")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expiry = datetime.fromisoformat(raw_date)
    if expiry > datetime.now(tz=pytz.utc):
        raise HTTPException(status_code=401, detail="Token has expired")

    ip = await redis.get(f"{user_id}-ip")
    if not ip or ip != client.host:
        raise HTTPException(status_code=401, detail="Invalid ip please reauthenticate")

    secret_b64, public_b64 = await asyncio.gather(
        redis.get(f"{user_id}-secret"),
        redis.get(f"{user_id}-public"),
    )
    if not secret_b64 or not public_b64:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    secret = Secret.from_b64(secret_b64)
    public = Public.from_b64(public_b64)
    user = await Psql().fetch_row(GET_USER_FROM_ID, user_id)

    return User(id=user["id"], name=user["name"], public=public, secret=secret)
