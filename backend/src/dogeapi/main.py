"""FastAPI application factory.

Builds the FastAPI app and wires only the modules whose ``FEATURE_*`` flag
is true. Disabled features incur zero runtime cost &mdash; their routers are
never registered, their optional Python deps never imported.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from dogeapi import __version__
from dogeapi.auth.password_reset import router as password_reset_router
from dogeapi.auth.router import router as auth_router
from dogeapi.auth.security import build_authx
from dogeapi.exceptions import install_exception_handlers
from dogeapi.organizations.router import router as orgs_router
from dogeapi.settings import Settings, get_settings

# Feature-gated routers are imported lazily inside ``create_app`` so a
# disabled feature's optional Python deps stay un-imported.


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """App lifespan: build per-app Redis client + AuthX, run feature setup."""
    settings: Settings = app.state.settings

    redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)
    app.state.redis = redis
    app.state.authx = build_authx(settings, redis=redis)

    if settings.FEATURE_LOGFIRE and settings.LOGFIRE_TOKEN:
        try:
            from dogeapi.observability import setup_logfire

            setup_logfire(app, settings)
        except ImportError:
            pass

    try:
        yield
    finally:
        await redis.aclose()
        audit_engine = getattr(app.state, "audit_engine", None)
        if audit_engine is not None:
            await audit_engine.dispose()
        rl_redis = getattr(app.state, "rate_limit_redis", None)
        if rl_redis is not None:
            await rl_redis.aclose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app.

    Args:
        settings: Optional pre-built ``Settings``. Mostly useful in tests
            where each test wants its own feature-flag combination.
    """
    settings = settings or get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=__version__,
        description="Multi-tenant SaaS boilerplate built on FastAPI + authx.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    install_exception_handlers(app)

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "version": __version__, "env": settings.APP_ENV}

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {"name": settings.APP_NAME, "version": __version__}

    app.include_router(auth_router)
    app.include_router(password_reset_router)
    app.include_router(orgs_router)

    if settings.FEATURE_API_KEYS:
        from dogeapi.api_keys.router import router as api_keys_router

        app.include_router(api_keys_router)

    if settings.FEATURE_AUDIT_LOG:
        from sqlalchemy import NullPool
        from sqlalchemy.ext.asyncio import create_async_engine

        from dogeapi.audit_log.middleware import AuditLogMiddleware
        from dogeapi.audit_log.router import router as audit_router

        # NullPool keeps the resource graph predictable in tests where the
        # ASGITransport doesn't run lifespan; in production the engine is
        # cheap to recreate per request and the dispose() in lifespan is the
        # final cleanup.
        audit_engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
            future=True,
        )
        app.state.audit_engine = audit_engine
        app.add_middleware(AuditLogMiddleware, engine=audit_engine)
        app.include_router(audit_router)

    if settings.FEATURE_RATE_LIMITING:
        from redis.asyncio import Redis

        from dogeapi.rate_limit.middleware import RateLimitPerIPMiddleware

        # Build a shared Redis client for the middleware (separate from the
        # per-request one used by deps). Closed on app shutdown.
        rl_redis = Redis.from_url(settings.REDIS_URL, decode_responses=False)
        app.state.rate_limit_redis = rl_redis
        app.add_middleware(
            RateLimitPerIPMiddleware,
            redis=rl_redis,
            per_minute=settings.RATE_LIMIT_PER_IP_PER_MINUTE,
        )

    if settings.FEATURE_OAUTH:
        from starlette.middleware.sessions import SessionMiddleware

        from dogeapi.oauth.client import build_oauth
        from dogeapi.oauth.router import router as oauth_router

        app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)
        app.state.oauth = build_oauth(settings)
        app.include_router(oauth_router)

    if settings.FEATURE_MAGIC_LINK:
        from dogeapi.magic_link.router import router as magic_router

        app.include_router(magic_router)

    if settings.FEATURE_STRIPE:
        from dogeapi.billing.router import router as billing_router

        app.include_router(billing_router)

    if settings.FEATURE_AI_CHAT:
        from dogeapi.ai.router import router as ai_router

        app.include_router(ai_router)

    # Admin endpoints are always-on; the dependency rejects non-superadmins.
    from dogeapi.admin.router import router as admin_router

    app.include_router(admin_router)

    return app


app = create_app()
