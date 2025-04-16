from pydantic import BaseModel


class SetPasswordOut(BaseModel):
    name: str
    success: bool = True
