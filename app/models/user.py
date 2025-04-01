from lwe import Public, Secret
from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    public_key: Public
    secret_key: Secret
