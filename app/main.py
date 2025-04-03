import os
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import asyncpg
import bcrypt
import uvicorn
from db.psql.client import Psql
from db.psql.users.queries import ADD_USER
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from models.authenticate.output import AuthOut
from models.new.inbound import NewIn
from models.new.outbound import NewOut
from routes.authenticate.auth import authenticate_user

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    async with Psql():
        yield


app = FastAPI(lifespan=lifespan)

if salt := os.getenv("SALT"):
    SALT = salt.encode()
else:
    raise ValueError("SALT not set")


@app.post("/new")
async def new(user: NewIn) -> NewOut:
    try:
        await Psql().execute(ADD_USER, str(uuid.uuid4()), user.username, bcrypt.hashpw(user.password.encode(), SALT))
    except asyncpg.PostgresError:
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return NewOut(username=user.username)


@app.post("/authenticate")
async def authenticate(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], public_key: str, request: Request
) -> AuthOut:
    return await authenticate_user(form_data, public_key, request)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
