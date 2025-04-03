from pydantic import BaseModel


class SetPasswordIn(BaseModel):
    username: str
    password: str
