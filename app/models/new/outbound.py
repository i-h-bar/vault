from pydantic import BaseModel


class NewOut(BaseModel):
    username: str
