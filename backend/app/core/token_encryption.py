from cryptography.fernet import Fernet, InvalidToken

from app.core.settings import get_settings


class TokenEncryptionError(ValueError):
    pass


def _get_fernet() -> Fernet:
    settings = get_settings()

    if not settings.token_encryption_key:
        raise TokenEncryptionError("TOKEN_ENCRYPTION_KEY is not configured.")

    key = settings.token_encryption_key.get_secret_value()

    try:
        return Fernet(key.encode("utf-8"))
    except ValueError as exc:
        raise TokenEncryptionError("TOKEN_ENCRYPTION_KEY is invalid.") from exc


def encrypt_token(raw_token: str) -> str:
    if not raw_token:
        raise TokenEncryptionError("Cannot encrypt an empty token.")

    fernet = _get_fernet()
    return fernet.encrypt(raw_token.encode("utf-8")).decode("utf-8")


def decrypt_token(encrypted_token: str) -> str:
    if not encrypted_token:
        raise TokenEncryptionError("Cannot decrypt an empty token.")

    fernet = _get_fernet()

    try:
        return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise TokenEncryptionError("Encrypted token could not be decrypted.") from exc
