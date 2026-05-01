"""Smoke tests for the billing module (P9).

We don't hit real Stripe; we verify endpoint wiring, scope checks, and
that the local subscription/limits machinery is correctly returned.
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

PASSWORD = "correct horse battery staple"


@pytest.fixture
async def billing_client(db_session: AsyncSession, redis_client: Redis) -> AsyncIterator[AsyncClient]:
    get_settings.cache_clear()
    settings = Settings(
        APP_ENV="test",
        JWT_SECRET_KEY="test-secret-please-do-not-use-in-prod-32-chars",
        DATABASE_URL=TEST_DB_URL_ASYNC,
        DATABASE_URL_SYNC=TEST_DB_URL_SYNC,
        REDIS_URL=TEST_REDIS_URL,
        FEATURE_STRIPE=True,
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


async def _signup_owner_with_org(client: AsyncClient) -> dict[str, str]:
    r = await client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": PASSWORD},
    )
    body = r.json()
    headers = {"Authorization": f"Bearer {body['tokens']['access_token']}"}
    await client.post("/orgs", json={"name": "Acme", "slug": "acme"}, headers=headers)
    switch = await client.post("/orgs/acme/switch", headers=headers)
    return {"Authorization": f"Bearer {switch.json()['access_token']}"}


class TestSubscription:
    async def test_returns_default_free_plan_with_limits(self, billing_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(billing_client)
        response = await billing_client.get("/orgs/acme/billing/subscription", headers=owner)
        assert response.status_code == 200
        body = response.json()
        assert body["plan"] == "free"
        assert body["limits"]["max_members"] == 5
        assert body["limits"]["max_api_keys"] == 2

    async def test_usage_endpoint_counts_members(self, billing_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(billing_client)
        response = await billing_client.get("/orgs/acme/billing/usage", headers=owner)
        assert response.status_code == 200
        body = response.json()
        assert body["members"] == 1
        assert body["api_keys"] == 0


class TestCheckout:
    async def test_returns_503_when_stripe_not_configured(self, billing_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(billing_client)
        response = await billing_client.post(
            "/orgs/acme/billing/checkout",
            json={"plan": "pro"},
            headers=owner,
        )
        assert response.status_code == 503

    async def test_invalid_plan_returns_400(self, billing_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(billing_client)
        response = await billing_client.post(
            "/orgs/acme/billing/checkout",
            json={"plan": "diamond"},
            headers=owner,
        )
        assert response.status_code == 400


class TestRBAC:
    async def test_member_cannot_open_checkout(self, billing_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(billing_client)
        invite = await billing_client.post(
            "/orgs/acme/invitations",
            json={"email": "bob@example.com", "role": "member"},
            headers=owner,
        )
        token = invite.json()["invite_link"].split("token=", 1)[1]
        bob = await billing_client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": PASSWORD},
        )
        bh = {"Authorization": f"Bearer {bob.json()['tokens']['access_token']}"}
        await billing_client.post("/invitations/accept", json={"token": token}, headers=bh)
        switch = await billing_client.post("/orgs/acme/switch", headers=bh)
        bob_scoped = {"Authorization": f"Bearer {switch.json()['access_token']}"}

        response = await billing_client.post(
            "/orgs/acme/billing/checkout",
            json={"plan": "pro"},
            headers=bob_scoped,
        )
        assert response.status_code == 403
