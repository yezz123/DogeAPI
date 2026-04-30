"""Tests for rate limiting (P6).

The per-IP middleware uses Redis fixed-window counters; we exercise it by
making more requests than the configured per-minute cap and asserting the
expected 429.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.db import get_session
from dogeapi.deps import get_redis
from dogeapi.main import create_app
from dogeapi.settings import Settings, get_settings
from tests.conftest import TEST_DB_URL_ASYNC, TEST_DB_URL_SYNC, TEST_REDIS_URL

pytestmark = pytest.mark.integration


@pytest.fixture
def rate_limited_settings() -> Iterator[Settings]:
    """Settings with FEATURE_RATE_LIMITING on and a tight per-minute cap."""
    get_settings.cache_clear()
    s = Settings(
        APP_ENV="test",
        JWT_SECRET_KEY="test-secret-please-do-not-use-in-prod-32-chars",
        DATABASE_URL=TEST_DB_URL_ASYNC,
        DATABASE_URL_SYNC=TEST_DB_URL_SYNC,
        REDIS_URL=TEST_REDIS_URL,
        FEATURE_API_KEYS=False,
        FEATURE_AUDIT_LOG=False,
        FEATURE_RATE_LIMITING=True,
        RATE_LIMIT_PER_IP_PER_MINUTE=3,
    )
    yield s
    get_settings.cache_clear()


@pytest.fixture
async def rl_client(
    rate_limited_settings: Settings,
    db_session: AsyncSession,
    redis_client: Redis,
) -> AsyncIterator[AsyncClient]:
    app = create_app(settings=rate_limited_settings)
    app.state.redis = redis_client

    from dogeapi.auth.security import build_authx

    app.state.authx = build_authx(rate_limited_settings, redis=redis_client)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def _override_redis() -> AsyncIterator[Redis]:
        yield redis_client

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_redis] = _override_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    rl_redis = getattr(app.state, "rate_limit_redis", None)
    if rl_redis is not None:
        await rl_redis.aclose()


class TestPerIPLimit:
    async def test_returns_429_after_threshold(self, rl_client: AsyncClient) -> None:
        """Configured limit is 3/min; the 4th request should be 429."""
        for _ in range(3):
            r = await rl_client.get("/healthz")
            assert r.status_code == 200, r.text

        blocked = await rl_client.get("/healthz")
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "60"
        assert blocked.json()["detail"] == "Too many requests"

    async def test_separate_ips_get_separate_buckets(self, rl_client: AsyncClient) -> None:
        """Different X-Forwarded-For IPs share no counters."""
        for _ in range(3):
            r = await rl_client.get("/healthz", headers={"X-Forwarded-For": "10.0.0.1"})
            assert r.status_code == 200

        # 10.0.0.1 is now exhausted
        blocked = await rl_client.get("/healthz", headers={"X-Forwarded-For": "10.0.0.1"})
        assert blocked.status_code == 429

        # ...but 10.0.0.2 has a fresh bucket
        fresh = await rl_client.get("/healthz", headers={"X-Forwarded-For": "10.0.0.2"})
        assert fresh.status_code == 200
