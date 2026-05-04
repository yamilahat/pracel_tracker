from app.worker.settings import WorkerSettings, worker_health_check


def test_worker_registers_health_check_function() -> None:
    assert WorkerSettings.functions == [worker_health_check]


def test_worker_redis_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://example-redis:6380/2")

    from app.worker.settings import build_redis_settings

    redis_settings = build_redis_settings("redis://example-redis:6380/2")

    assert redis_settings.host == "example-redis"
    assert redis_settings.port == 6380
    assert redis_settings.database == 2
