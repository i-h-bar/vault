from lwe import Public, Secret
from pytest import fixture


@fixture
def keys() -> tuple[Secret, Public]:
    secret = Secret()
    public = secret.generate_public_key()
    return secret, public


def test_keys() -> None:
    secret = Secret()
    public = secret.generate_public_key()
    assert isinstance(public, Public)


def test_encrypt(keys: tuple[Secret, Public]) -> None:
    secret, public = keys
    message = "Hello, world!"

    encrypted = public.encrypt(message)
    assert isinstance(encrypted, str)
    assert encrypted != message
    assert message not in encrypted


def test_decrypt(keys: tuple[Secret, Public]) -> None:
    secret, public = keys
    message = "Hello, world!"

    encrypted = public.encrypt(message)
    decrypted = secret.decrypt(encrypted)

    assert decrypted == message


def test_decrypt_ut8(keys: tuple[Secret, Public]) -> None:
    secret, public = keys
    message = "你好世界！"  # noqa: RUF001

    encrypted = public.encrypt(message)
    decrypted = secret.decrypt(encrypted)

    assert decrypted == message


def test_from_and_to_bytes(keys: tuple[Secret, Public]) -> None:
    secret, public = keys

    secret_bytes = secret.to_bytes()
    assert isinstance(secret_bytes, bytes)
    secret_2 = Secret.from_bytes(secret_bytes)

    public_bytes = public.to_bytes()
    assert isinstance(public_bytes, bytes)
    public_2 = Public.from_bytes(public_bytes)

    matrix = ((secret_2, public_2), (secret_2, public), (secret, public_2))

    message = "Hello, world!"
    for s_key, p_key in matrix:
        encrypted = p_key.encrypt(message)
        assert isinstance(encrypted, str)
        assert encrypted != message
        assert message not in encrypted
        decrypted = s_key.decrypt(encrypted)
        assert decrypted == message


def test_from_and_to_b64(keys: tuple[Secret, Public]) -> None:
    secret, public = keys

    secret_bytes = secret.to_b64()
    assert isinstance(secret_bytes, str)
    secret_2 = Secret.from_b64(secret_bytes)

    public_bytes = public.to_b64()
    assert isinstance(public_bytes, str)
    public_2 = Public.from_b64(public_bytes)

    matrix = ((secret_2, public_2), (secret_2, public), (secret, public_2))

    message = "Hello, world!"
    for s_key, p_key in matrix:
        encrypted = p_key.encrypt(message)
        assert isinstance(encrypted, str)
        assert encrypted != message
        assert message not in encrypted
        decrypted = s_key.decrypt(encrypted)
        assert decrypted == message
