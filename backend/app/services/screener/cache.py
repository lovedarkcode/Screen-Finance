"""Versioned public-data caches; bounded local fallback when Redis is unavailable."""
import asyncio
import hashlib
import json
from collections import deque
from time import monotonic
from fastapi import HTTPException
from app.core.cache import cache_get, cache_set, get_redis
from app.services.screener.metrics import SCHEMA_VERSION

_cache, _rates = {}, {}


def key_for(kind, value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return f"{SCHEMA_VERSION}:{kind}:" + hashlib.sha256(raw.encode()).hexdigest()


async def get(key):
    try:
        value = await asyncio.wait_for(cache_get(key), .3)
        if value is not None:
            return value
    except Exception:
        pass
    saved = _cache.get(key)
    return saved[1] if saved and saved[0] > monotonic() else None


async def put(key, value, ttl):
    if len(_cache) >= 256:
        _cache.pop(next(iter(_cache)))
    _cache[key] = (monotonic() + ttl, value)
    try:
        await asyncio.wait_for(cache_set(key, value, ttl=ttl), .3)
    except Exception:
        pass


async def rate_limit(user):
    key = f"{SCHEMA_VERSION}:rate:{user.id}"
    try:
        pipe = get_redis().pipeline(transaction=True)
        pipe.incr(key)
        pipe.expire(key, 60, nx=True)
        count, _ = await asyncio.wait_for(pipe.execute(), .3)
    except Exception:
        # ponytail: per-worker fallback; Redis enforces a shared limit across workers.
        now = monotonic()
        if len(_rates) >= 1024 and key not in _rates:
            _rates.pop(next(iter(_rates)))
        times = _rates.setdefault(key, deque())
        while times and times[0] <= now - 60:
            times.popleft()
        times.append(now)
        count = len(times)
    if count > 20:
        raise HTTPException(429, "Too many screening requests. Please retry in a minute.", headers={"Retry-After": "60"})
