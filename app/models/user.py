from lwe import Public, Secret
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str
    name: str
    public: Public
    secret: Secret
