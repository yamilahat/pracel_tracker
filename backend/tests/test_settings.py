from app.core.settings import Settings


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/app")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/1")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert settings.app_secret_key == "test-secret"
    assert settings.database_url == "postgresql+asyncpg://user:pass@db:5432/app"
    assert settings.redis_url == "redis://cache:6379/1"
