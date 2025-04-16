import uuid
from contextlib import asynccontextmanager
from hashlib import sha256
from typing import Annotated, AsyncGenerator

import uvicorn
from db.psql.client import Psql
from db.psql.passwords.queries import INSERT_PASSWORD
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.security import OAuth2PasswordRequestForm
from lwe.model_decrypt import decrypt_set_password
from models.authenticate.output import Token
from models.new.inbound import NewIn
from models.new.outbound import NewOut
from models.user import User
from routes.authenticate.auth import authenticate_user
from routes.new.new_user import create_user
from routes.password.post.inbound import SetPasswordIn
from routes.password.post.outbound import SetPasswordOut

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    async with Psql():
        yield


app = FastAPI(lifespan=lifespan)


@app.post("/new")
async def new(user: NewIn) -> NewOut:
    return await create_user(user)


@app.post("/authenticate")
async def authenticate(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request) -> Token:
    return await authenticate_user(form_data, request)


@app.post("/password")
async def set_password(payload: Annotated[tuple[SetPasswordIn, User], Depends(decrypt_set_password)]) -> SetPasswordOut:
    set_password_in, user = payload
    await Psql().execute(
        INSERT_PASSWORD,
        uuid.uuid4(),
        user.id,
        set_password_in.username,
        set_password_in.password,
        sha256(set_password_in.name.encode()).hexdigest(),
    )
    return SetPasswordOut(name=set_password_in.name)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
