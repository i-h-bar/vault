from pydantic import BaseModel


class SetPasswordOut(BaseModel):
    username: str
    success: bool = True
