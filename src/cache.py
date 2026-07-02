import redis

from src.config import settings

redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

TASK_LIST_CACHE_PREFIX = "tasks:list:"


def get_redis() -> redis.Redis:
    return redis_client


def build_task_list_cache_key(
    *,
    status: str | None,
    priority: str | None,
    tags: list[str] | None,
    sort_by: str,
    sort_order: str,
    offset: int,
    limit: int,
) -> str:
    tags_part = ",".join(sorted(tags)) if tags else ""
    return (
        f"{TASK_LIST_CACHE_PREFIX}status={status or ''}:priority={priority or ''}:"
        f"tags={tags_part}:sort_by={sort_by}:sort_order={sort_order}:offset={offset}:limit={limit}"
    )


def invalidate_task_list_cache(client: redis.Redis) -> None:
    keys = list(client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))
    if keys:
        client.delete(*keys)
