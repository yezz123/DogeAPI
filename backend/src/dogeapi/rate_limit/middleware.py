"""Per-IP rate limit middleware.

Always-on baseline that protects unauthenticated endpoints (login, register,
forgot-password). Authenticated finer-grained limits are applied via deps.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from authx import RateLimiter
from authx.exceptions import RateLimitExceeded
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from dogeapi.rate_limit.backend import RedisRateLimitBackend

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from starlette.requests import Request


def _ip_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    if request.client is not None:
        return f"ip:{request.client.host}"
    return "ip:unknown"


class RateLimitPerIPMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        redis: Redis,
        per_minute: int,
    ) -> None:
        super().__init__(app)
        backend = RedisRateLimitBackend(redis)
        self._limiter = RateLimiter(
            max_requests=per_minute,
            window=60,
            backend=backend,
            key_func=_ip_key,
        )

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        try:
            await self._limiter(request)
        except RateLimitExceeded:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
