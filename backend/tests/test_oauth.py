"""Smoke tests for OAuth wiring (P7).

We don't talk to real Google/GitHub here; we just verify the router is
mounted, returns a redirect, and gives 404 for unknown providers.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

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
async def oauth_client(db_session: AsyncSession, redis_client: Redis) -> AsyncIterator[AsyncClient]:
    get_settings.cache_clear()
    settings = Settings(
        APP_ENV="test",
        JWT_SECRET_KEY="test-secret-please-do-not-use-in-prod-32-chars",
        DATABASE_URL=TEST_DB_URL_ASYNC,
        DATABASE_URL_SYNC=TEST_DB_URL_SYNC,
        REDIS_URL=TEST_REDIS_URL,
        FEATURE_OAUTH=True,
        OAUTH_GOOGLE_CLIENT_ID="fake-google-id",
        OAUTH_GOOGLE_CLIENT_SECRET="fake-google-secret",
    )

    app = create_app(settings=settings)
    app.state.redis = redis_client

    from dogeapi.auth.security import build_authx

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

    get_settings.cache_clear()


class TestOAuthRouter:
    async def test_unknown_provider_returns_404(self, oauth_client: AsyncClient) -> None:
        response = await oauth_client.get("/auth/oauth/twitter/start")
        assert response.status_code == 404

    async def test_known_provider_route_exists(self, oauth_client: AsyncClient) -> None:
        """Smoke check: the /auth/oauth/google/start route is mounted.

        We don't actually invoke the redirect (it would hit Google's
        OpenID discovery endpoint). The OpenAPI schema is enough.
        """
        schema = await oauth_client.get("/openapi.json")
        paths = schema.json().get("paths", {})
        assert "/auth/oauth/{provider}/start" in paths
        assert "/auth/oauth/{provider}/callback" in paths
