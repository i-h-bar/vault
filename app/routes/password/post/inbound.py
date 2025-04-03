from pydantic import BaseModel


class SetPasswordIn(BaseModel):
    name: str
    password: str
