from pydantic import BaseModel


class SetPasswordIn(BaseModel):
    password: str
    name: str
    username: str | None = None
