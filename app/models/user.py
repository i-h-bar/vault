from lwe import Public, Secret
from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str
    public: Public
    secret: Secret
