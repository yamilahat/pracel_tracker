from urllib.parse import urlparse

from arq.connections import RedisSettings

from app.core.settings import get_settings


async def worker_health_check(ctx: dict) -> str:
    return "ok"


def build_redis_settings(redis_url: str) -> RedisSettings:
    parsed_url = urlparse(redis_url)
    database = parsed_url.path.lstrip("/")

    return RedisSettings(
        host=parsed_url.hostname or "localhost",
        port=parsed_url.port or 6379,
        database=int(database or 0),
        password=parsed_url.password,
    )


class WorkerSettings:
    functions = [worker_health_check]
    redis_settings = build_redis_settings(get_settings().redis_url)
