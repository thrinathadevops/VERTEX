# PATH: varex_backend/app/services/token_blacklist.py
# Redis-backed JWT blacklist for logout and token revocation

import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT ID to the blacklist. TTL = remaining token lifetime."""
    import redis.exceptions
    try:
        r = await get_redis()
        await r.setex(f"blacklist:{jti}", ttl_seconds, "1")
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        from app.core.logger import structured_logger
        structured_logger.warning(f"redis is not available, skipping blacklist for {jti}")


async def is_blacklisted(jti: str) -> bool:
    import redis.exceptions
    try:
        r = await get_redis()
        return bool(await r.exists(f"blacklist:{jti}"))
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        from app.core.logger import structured_logger
        structured_logger.warning(f"redis is not available, assuming {jti} is not blacklisted")
        return False


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
