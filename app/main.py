import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import asyncpg
import bcrypt
import uvicorn
from asyncpg import Pool
from db import pool
from db.users.queries import ADD_USER
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from lwe import Public, Secret
from models.authenticate.token import Token
from models.new.inbound import NewIn
from models.new.outbound import NewOut
from models.output import EncryptedOutput
from models.session.inbound import SessionIn
from redis.asyncio import Redis
from routes.authenticate.auth import authenticate_user

load_dotenv()

redis = Redis()

pool: Pool


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    global pool

    pool = await asyncpg.create_pool(dsn=os.getenv("PSQL_URI"))
    yield
    await pool.close()


app = FastAPI(lifespan=lifespan)

if salt := os.getenv("SALT"):
    SALT = salt.encode()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World!"}


@app.post("/new")
async def new(user: NewIn) -> NewOut:
    try:
        await pool.execute(ADD_USER, str(uuid.uuid4()), user.username, bcrypt.hashpw(user.password.encode(), SALT))
    except asyncpg.PostgresError:
        raise HTTPException(status_code=500, detail="Internal Server Error")  # noqa: B904

    return NewOut(username=user.username)


@app.post("/authenticate")
async def authenticate(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], public_key: str) -> Token:
    global redis

    return await authenticate_user(form_data, public_key, pool, redis)


@app.post("/session")
async def session(session_in: SessionIn, request: Request) -> EncryptedOutput:
    if client := request.client:
        client_ip = client.host
    else:
        raise HTTPException(status_code=400, detail="Client not found")

    client_public_key_b64 = session_in.pub_key
    client_public_key = Public.from_b64(client_public_key_b64)

    app_secret = Secret()
    app_public_key = app_secret.generate_public_key().to_b64()
    app_public_key_encrypted = client_public_key.encrypt(app_public_key)

    redis_keys = {
        "secret": app_secret.to_b64(),
        "public": client_public_key_b64,
    }

    await redis.set(client_ip, json.dumps(redis_keys), ex=1800)

    return EncryptedOutput(content=app_public_key_encrypted)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
