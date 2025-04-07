from fastapi.security import OAuth2PasswordRequestForm
from lwe import Secret
from pytest import fixture, mark

SECRET = Secret()
PUBLIC = SECRET.generate_public_key()


@fixture
def form_data() -> OAuth2PasswordRequestForm:
    return OAuth2PasswordRequestForm(
        username="test",
        password="password",  # noqa: S106
        client_secret=PUBLIC.to_b64(),
    )


@mark.asyncio
async def test_auth_positive_flow(form_data: OAuth2PasswordRequestForm) -> None: ...
