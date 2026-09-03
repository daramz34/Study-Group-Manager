import json
import redis
from core.config import settings

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
except Exception:
    print("⚠️ Redis not available — caching disabled")
    REDIS_AVAILABLE = False


def get_cached(key: str):
    """Get from cache, return None if miss or Redis unavailable"""
    if not REDIS_AVAILABLE:
        return None
    try:
        cached = redis_client.get(key)
        return json.loads(cached) if cached else None
    except Exception:
        return None


def set_cache(key: str, data, ttl_seconds: int = 300):
    """Set cache with TTL, skip if Redis unavailable"""
    if not REDIS_AVAILABLE:
        return
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(data, default=str))
    except Exception:
        pass


def invalidate_cache(pattern: str):
    """Delete keys matching pattern, skip if Redis unavailable"""
    if not REDIS_AVAILABLE:
        return
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass
