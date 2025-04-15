from pydantic import BaseModel


class EncryptedInput(BaseModel):
    content: str
