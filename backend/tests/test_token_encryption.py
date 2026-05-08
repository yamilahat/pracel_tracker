import pytest
from app.core.settings import get_settings
from app.core.token_encryption import (
    TokenEncryptionError,
    decrypt_token,
    encrypt_token,
)
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_encrypt_and_decrypt_token(monkeypatch) -> None:
    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", key)

    encrypted = encrypt_token("gmail-access-token")

    assert encrypted != "gmail-access-token"
    assert decrypt_token(encrypted) == "gmail-access-token"


def test_encrypt_requires_key(monkeypatch) -> None:
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "")

    with pytest.raises(TokenEncryptionError):
        encrypt_token("gmail-access-token")


def test_decrypt_rejects_invalid_token(monkeypatch) -> None:
    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", key)

    with pytest.raises(TokenEncryptionError):
        decrypt_token("not-a-valid-encrypted-token")
