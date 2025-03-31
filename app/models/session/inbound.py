from pydantic import BaseModel


class SessionIn(BaseModel):
    pub_key: str
