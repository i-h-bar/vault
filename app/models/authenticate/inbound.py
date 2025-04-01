from fastapi.security import OAuth2PasswordRequestForm


class AuthIn(OAuth2PasswordRequestForm):
    public_key: str
