"""Redis-backed rate-limit storage that implements authx's protocol.

Uses a fixed-window counter: ``INCR key`` followed by ``EXPIRE key window``
when count is 1. Cheap, stateless, and accurate enough for HTTP rate limits.
"""

from __future__ import annotations

from redis.asyncio import Redis


class RedisRateLimitBackend:
    """authx ``RateLimitBackend`` implementation backed by Redis."""

    def __init__(self, redis: Redis, *, prefix: str = "ratelimit:") -> None:
        self._redis = redis
        self._prefix = prefix

    async def increment(self, key: str, window: int) -> int:
        full_key = f"{self._prefix}{key}"
        pipe = self._redis.pipeline()
        pipe.incr(full_key)
        pipe.expire(full_key, window, nx=True)
        count, _ = await pipe.execute()
        return int(count)

    async def reset(self, key: str) -> None:
        await self._redis.delete(f"{self._prefix}{key}")
