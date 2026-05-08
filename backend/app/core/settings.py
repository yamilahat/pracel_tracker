from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="local", validation_alias="APP_ENV")
    app_secret_key: str = Field(
        default="change-this-local-secret",
        validation_alias="APP_SECRET_KEY",
    )
    database_url: str = Field(
        default="postgresql+asyncpg://parcel_tracker:parcel_tracker@localhost:5432/parcel_tracker",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    token_encryption_key: SecretStr | None = Field(
        default=None, validation_alias="TOKEN_ENCRYPTION_KEY"
    )
    google_client_id: str | None = Field(
        default=None, validation_alias="GOOGLE_CLIENT_ID"
    )
    google_client_secret: SecretStr | None = Field(
        default=None, validation_alias="GOOGLE_CLIENT_SECRET"
    )
    google_redirect_uri: str = Field(
        default="http://localhost:8000/auth/gmail/callback",
        validation_alias="GOOGLE_REDIRECT_URI",
    )
    gmail_oauth_scopes: list[str] = Field(
        default=["https://www.googleapis.com/auth/gmail.metadata"],
        validation_alias="GMAIL_OAUTH_SCOPES",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
