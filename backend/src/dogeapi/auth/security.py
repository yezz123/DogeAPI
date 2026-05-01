"""authx wiring: a single ``AuthX`` instance built from app settings.

We wrap construction in :func:`build_authx` so tests can inject custom
settings, and we cache the production instance per ``Settings`` object via
:func:`get_authx`.
"""

from __future__ import annotations

from functools import lru_cache

from authx import AuthX, AuthXConfig
from redis.asyncio import Redis

from dogeapi.settings import Settings, get_settings


def _make_config(settings: Settings) -> AuthXConfig:
    return AuthXConfig(
        JWT_ALGORITHM=settings.JWT_ALGORITHM,  # type: ignore[arg-type]
        JWT_SECRET_KEY=settings.JWT_SECRET_KEY,
        JWT_ACCESS_TOKEN_EXPIRES=settings.jwt_access_expires,
        JWT_REFRESH_TOKEN_EXPIRES=settings.jwt_refresh_expires,
        JWT_TOKEN_LOCATION=["headers", "cookies"],  # type: ignore[arg-type]
        JWT_COOKIE_SECURE=settings.JWT_COOKIE_SECURE,
        JWT_COOKIE_SAMESITE=settings.JWT_COOKIE_SAMESITE,  # type: ignore[arg-type]
        JWT_COOKIE_CSRF_PROTECT=True,
        JWT_SESSION_TRACKING=False,
    )


def build_authx(settings: Settings, redis: Redis | None = None) -> AuthX:
    """Construct an ``AuthX`` instance + wire token blocklist to Redis.

    Args:
        settings: Application settings.
        redis: Optional async redis client. When provided, refresh+access
            tokens can be revoked via :meth:`AuthX.set_token_blocklist`
            so logout takes immediate effect across replicas.
    """
    auth: AuthX = AuthX(config=_make_config(settings))

    if redis is not None:

        async def is_blocked(token: str) -> bool:
            return bool(await redis.get(f"blocklist:{token}"))

        auth.set_callback_token_blocklist(is_blocked)

    return auth


@lru_cache(maxsize=1)
def get_authx() -> AuthX:
    """Process-wide ``AuthX`` instance (no Redis blocklist).

    For request-scoped use ``app.state.authx`` set up in :mod:`dogeapi.main`.
    """
    return build_authx(get_settings())
