from pydantic import BaseModel


class NewIn(BaseModel):
    username: str
    password: str
