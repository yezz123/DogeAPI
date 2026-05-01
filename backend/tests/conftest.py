"""Shared pytest fixtures.

We rely on a live Postgres + Redis (started by ``docker compose -f
infra/docker-compose.yml up``). Each test runs inside a SAVEPOINT-wrapped
transaction that is rolled back at teardown so tests are fully isolated
without paying the cost of recreating the schema.

Redis isolation: the test fixture uses DB 15 and ``FLUSHDB`` between tests.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from dogeapi.db import get_session
from dogeapi.main import create_app
from dogeapi.settings import Settings, get_settings

TEST_DB_NAME = "dogeapi_test"
TEST_DB_URL_ASYNC = f"postgresql+asyncpg://dogeapi:dogeapi@localhost:5432/{TEST_DB_NAME}"
TEST_DB_URL_SYNC = f"postgresql+psycopg://dogeapi:dogeapi@localhost:5432/{TEST_DB_NAME}"
TEST_REDIS_URL = "redis://localhost:6379/15"


def _ensure_test_database() -> None:
    """Create + migrate the test database if it doesn't already exist."""
    import psycopg

    with (
        psycopg.connect(
            "postgresql://dogeapi:dogeapi@localhost:5432/postgres",
            autocommit=True,
        ) as conn,
        conn.cursor() as cur,
    ):
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{TEST_DB_NAME}" OWNER dogeapi')

    with psycopg.connect(f"postgresql://dogeapi:dogeapi@localhost:5432/{TEST_DB_NAME}") as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
            cur.execute('CREATE EXTENSION IF NOT EXISTS "citext"')
        conn.commit()


def _run_migrations() -> None:
    """Run alembic migrations against the test database."""
    from alembic import command
    from alembic.config import Config

    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(backend_root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_root, "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL_SYNC)
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session", autouse=True)
def _bootstrap_test_db() -> Iterator[None]:
    """Create the test DB + run migrations once per test session."""
    _ensure_test_database()
    _run_migrations()
    yield


@pytest.fixture
def settings(request: pytest.FixtureRequest) -> Iterator[Settings]:
    """Test-friendly settings.

    Override individual flags via ``@pytest.mark.feature_flags(audit_log=True)``.
    Default values keep audit-log + rate-limiting off so most tests don't
    pay their cost or pollute the test DB.
    """
    get_settings.cache_clear()
    overrides: dict[str, bool] = {}
    marker = request.node.get_closest_marker("feature_flags")
    if marker is not None:
        overrides = marker.kwargs

    s = Settings(
        APP_ENV="test",
        JWT_SECRET_KEY="test-secret-please-do-not-use-in-prod-32-chars",
        DATABASE_URL=TEST_DB_URL_ASYNC,
        DATABASE_URL_SYNC=TEST_DB_URL_SYNC,
        REDIS_URL=TEST_REDIS_URL,
        FEATURE_API_KEYS=overrides.get("api_keys", True),
        FEATURE_AUDIT_LOG=overrides.get("audit_log", False),
        FEATURE_RATE_LIMITING=overrides.get("rate_limiting", False),
        FEATURE_OAUTH=overrides.get("oauth", False),
        FEATURE_MAGIC_LINK=overrides.get("magic_link", False),
        FEATURE_EMAIL_DELIVERY=overrides.get("email_delivery", False),
        FEATURE_AI_CHAT=overrides.get("ai_chat", False),
        FEATURE_LOGFIRE=overrides.get("logfire", False),
        FEATURE_STRIPE=overrides.get("stripe", False),
    )
    yield s
    get_settings.cache_clear()


@pytest.fixture
async def db_session(settings: Settings) -> AsyncIterator[AsyncSession]:
    """Per-test session bound to an outer transaction that is rolled back.

    Uses SQLAlchemy's ``join_transaction_mode="create_savepoint"`` so any
    ``session.commit()`` performed by application code only releases a
    SAVEPOINT, leaving the outer transaction intact for teardown rollback.
    """
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async with engine.connect() as connection:
        trans = await connection.begin()
        factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
            join_transaction_mode="create_savepoint",
        )
        async with factory() as session:
            yield session
        await trans.rollback()
    await engine.dispose()


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    """A flushed Redis client on the test DB."""
    client = Redis.from_url(TEST_REDIS_URL, decode_responses=False)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest.fixture
async def client(
    settings: Settings,
    db_session: AsyncSession,
    redis_client: Redis,
) -> AsyncIterator[AsyncClient]:
    """In-process test client with overridden DB and lifespan-skipped Redis.

    We override ``get_session`` to hand the SAVEPOINT-wrapped session to
    every endpoint so writes performed during the test are visible inside
    the same transaction and rolled back at teardown.
    """
    app = create_app(settings=settings)
    app.state.redis = redis_client

    from dogeapi.auth.security import build_authx
    from dogeapi.deps import get_redis

    app.state.authx = build_authx(settings, redis=redis_client)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def _override_redis() -> AsyncIterator[Redis]:
        yield redis_client

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_redis] = _override_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    audit_engine = getattr(app.state, "audit_engine", None)
    if audit_engine is not None:
        await audit_engine.dispose()
