"""Postgres-specific helpers (raw asyncpg pool for high-throughput jobs)."""
from __future__ import annotations

import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


async def get_pg_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        dsn = settings.DATABASE_URL.replace("+asyncpg", "")
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)
    return _pool


async def close_pg_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
