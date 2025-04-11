import uuid

import asyncpg
import bcrypt
from db.psql.client import Psql
from db.psql.users.queries import ADD_USER
from fastapi import HTTPException
from main import SALT
from models.new.inbound import NewIn
from models.new.outbound import NewOut


async def create_user(user: NewIn) -> NewOut:
    try:
        await Psql().execute(ADD_USER, str(uuid.uuid4()), user.username, bcrypt.hashpw(user.password.encode(), SALT))
    except asyncpg.PostgresError:
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return NewOut(username=user.username)
