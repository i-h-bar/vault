from pydantic import BaseModel


class GetPasswordIn(BaseModel):
    name: str


class GetPasswordOut(BaseModel):
    username: str
    password: str
