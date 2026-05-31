"""Async Redis cache wrapper with JSON serialization."""
from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from app.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


async def cache_get(key: str) -> Any | None:
    raw = await get_redis().get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    await get_redis().set(key, json.dumps(value), ex=ttl)


async def cache_delete(key: str) -> None:
    await get_redis().delete(key)
