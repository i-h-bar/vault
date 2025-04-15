import json
from typing import Annotated

import pydantic
from fastapi import Depends, HTTPException
from models.input import EncryptedInput
from models.user import User
from routes.authenticate.current_user import get_current_user
from routes.password.post.inbound import SetPasswordIn


async def decrypt(model: EncryptedInput, user: Annotated[User, Depends(get_current_user)]) -> tuple[User, str]:
    return user, user.secret.decrypt(model.content)


async def decrypt_set_password(payload: Annotated[tuple[User, str], Depends(decrypt)]) -> tuple[SetPasswordIn, User]:
    user, message = payload

    try:
        message = json.loads(message)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Bad Input")

    try:
        set_password_in = SetPasswordIn(**message)
    except pydantic.ValidationError:
        raise HTTPException(status_code=400, detail="Bad Input")

    return set_password_in, user
