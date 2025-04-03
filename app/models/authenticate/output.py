from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    public_key: str
    token_type: str = "bearer"  # noqa: S105
