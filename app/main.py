import os
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import uvicorn
from db.psql.client import Psql
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.security import OAuth2PasswordRequestForm
from models.authenticate.output import Token
from models.new.inbound import NewIn
from models.new.outbound import NewOut
from models.user import User
from routes.authenticate.auth import authenticate_user
from routes.authenticate.current_user import get_current_user
from routes.new.new_user import create_user
from routes.password.post.inbound import SetPasswordIn
from routes.password.post.outbound import SetPasswordOut

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
    return await create_user(user)


@app.post("/authenticate")
async def authenticate(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request) -> Token:
    return await authenticate_user(form_data, request)


@app.post("/password")
async def set_password(_: SetPasswordIn, __: Annotated[User, Depends(get_current_user)]) -> SetPasswordOut:
    return SetPasswordOut()


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
