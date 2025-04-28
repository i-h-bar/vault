import uuid
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import bcrypt
import uvicorn
from db.psql.client import Psql
from db.psql.passwords.queries import GET_PASSWORD, INSERT_PASSWORD
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.security import OAuth2PasswordRequestForm
from lwe.model_decrypt import decrypt_get_password, decrypt_set_password
from models.authenticate.output import Token
from models.new.inbound import NewIn
from models.new.outbound import NewOut
from models.password.get import GetPasswordIn, GetPasswordOut
from models.user import User
from routes.authenticate.auth import authenticate_user
from routes.new.new_user import create_user
from routes.password.post.constants import USER_SALT
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
        bcrypt.hashpw(set_password_in.name.encode(), salt=USER_SALT),
    )
    return SetPasswordOut(name=set_password_in.name)


@app.get("/password")
async def get_password(
    payload: Annotated[tuple[GetPasswordIn, User], Depends(decrypt_get_password)],
) -> GetPasswordOut:  # TODO: Add base model to encrypt output before sending
    get_password_in, user = payload

    row = await Psql().fetch_row(
        GET_PASSWORD,
        bcrypt.hashpw(get_password_in.name.encode(), salt=USER_SALT),
        user.id,
    )

    return GetPasswordOut(username=row["username"], password=row["password"])


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
