from pydantic import BaseModel


class Token(BaseModel):
    token: str
    type: str = "bearer"
