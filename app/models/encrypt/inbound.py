from pydantic import BaseModel


class EncryptIn(BaseModel):
    message: str