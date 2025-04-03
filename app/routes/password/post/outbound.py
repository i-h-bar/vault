from pydantic import BaseModel


class SetPasswordOut(BaseModel):
    success: bool = True
