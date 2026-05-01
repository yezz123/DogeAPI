"""Magic-link tokens persisted in Redis (no DB table needed)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from redis.asyncio import Redis

PREFIX = "magiclink:"


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def issue(redis: Redis, email: str, *, ttl: timedelta) -> str:
    token = secrets.token_urlsafe(32)
    await redis.setex(
        f"{PREFIX}{_hash(token)}",
        int(ttl.total_seconds()),
        email,
    )
    return token


async def consume(redis: Redis, token: str) -> str | None:
    """Validate and atomically delete a magic-link token. Returns email or None."""
    key = f"{PREFIX}{_hash(token)}"
    pipe = redis.pipeline()
    pipe.get(key)
    pipe.delete(key)
    raw, _ = await pipe.execute()
    if not raw:
        return None
    return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
