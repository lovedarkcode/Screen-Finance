"""Redis client (re-exported from core.cache for db-layer access)."""
from app.core.cache import cache_delete, cache_get, cache_set, get_redis

__all__ = ["get_redis", "cache_get", "cache_set", "cache_delete"]
