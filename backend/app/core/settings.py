from functools import lru_cache

from pydantic import Field
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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
