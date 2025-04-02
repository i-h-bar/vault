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
from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from models.authenticate.output import AuthOut
from models.new.inbound import NewIn
from models.new.outbound import NewOut
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
async def authenticate(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], public_key: str) -> AuthOut:
    return await authenticate_user(form_data, public_key, pool, redis)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
