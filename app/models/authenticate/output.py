from pydantic import BaseModel


class Token(BaseModel):
    token: str
    type: str = "bearer"


class AuthOut(BaseModel):
    token: Token
    public_key: str
