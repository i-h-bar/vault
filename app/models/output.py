from pydantic import BaseModel


class EncryptedOutput(BaseModel):
    content: str
