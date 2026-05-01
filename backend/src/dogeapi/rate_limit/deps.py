"""FastAPI dep factories for finer-grained rate limits.

Each factory returns a coroutine dep that applies an authx ``RateLimiter``
keyed by the appropriate identity:

- :func:`rate_limit_per_user` &mdash; requires JWT, keyed by ``sub``
- :func:`rate_limit_per_org` &mdash; requires org-scoped JWT, keyed by ``org_id``
- :func:`rate_limit_per_api_key` &mdash; requires X-API-Key, keyed by key id

Apply with::

    @router.get(
        "/heavy-route",
        dependencies=[Depends(rate_limit_per_user(per_minute=60))],
    )
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from authx import RateLimiter, TokenPayload
from fastapi import Depends, Request

from dogeapi.api_keys.dependencies import api_key_payload
from dogeapi.deps import _token_extra, get_redis, get_token_payload
from dogeapi.rate_limit.backend import RedisRateLimitBackend


def _build(per_minute: int, key_func: Callable[[Request], str]) -> RateLimiter:
    """Lazy-built so each dep gets its own limiter (each backed by current redis)."""
    return RateLimiter(
        max_requests=per_minute,
        window=60,
        key_func=key_func,
    )


def rate_limit_per_user(per_minute: int) -> Callable[..., Awaitable[None]]:
    async def _check(
        request: Request,
        payload: Annotated[TokenPayload, Depends(get_token_payload)],
        redis=Depends(get_redis),
    ) -> None:
        backend = RedisRateLimitBackend(redis)
        limiter = RateLimiter(
            max_requests=per_minute,
            window=60,
            backend=backend,
            key_func=lambda _r: f"user:{payload.sub}",
        )
        await limiter(request)

    return _check


def rate_limit_per_org(per_minute: int) -> Callable[..., Awaitable[None]]:
    async def _check(
        request: Request,
        payload: Annotated[TokenPayload, Depends(get_token_payload)],
        redis=Depends(get_redis),
    ) -> None:
        org_id = _token_extra(payload, "org_id") or "none"
        backend = RedisRateLimitBackend(redis)
        limiter = RateLimiter(
            max_requests=per_minute,
            window=60,
            backend=backend,
            key_func=lambda _r: f"org:{org_id}",
        )
        await limiter(request)

    return _check


def rate_limit_per_api_key(per_minute: int) -> Callable[..., Awaitable[None]]:
    async def _check(
        request: Request,
        payload: Annotated[TokenPayload | None, Depends(api_key_payload)],
        redis=Depends(get_redis),
    ) -> None:
        if payload is None:
            return  # if no API key, this dep is a no-op
        api_key_id = _token_extra(payload, "api_key_id") or "none"
        backend = RedisRateLimitBackend(redis)
        limiter = RateLimiter(
            max_requests=per_minute,
            window=60,
            backend=backend,
            key_func=lambda _r: f"apikey:{api_key_id}",
        )
        await limiter(request)

    return _check


__all__ = (
    "rate_limit_per_api_key",
    "rate_limit_per_org",
    "rate_limit_per_user",
)


# Use _build to keep linters happy (it's a documented helper).
_ = _build
