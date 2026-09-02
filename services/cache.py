import json
import redis
from core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_cached(key:str):
    """Get from cache, return None if miss"""

    cached = redis_client.get(key)
    return json.loads(cached) if cached else None


def set_cache(key:str, data, ttl_seconds: int= 300):
    """Set cache with TTL (default 5 minutes)"""
    redis_client.setex(key, ttl_seconds, json.dumps(data, default=str))


def invalidate_cache(pattern: str):
    """Delete all keys matching pattern"""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
    