from pydantic import BaseModel


class EncryptOut(BaseModel):
    encrypted: str
