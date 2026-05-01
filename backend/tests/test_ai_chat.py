"""Tests for the AI chat module (P10).

We rely on the deterministic ``_EchoAgent`` fallback that's selected when
no LLM API key is configured. This means the tests run fully offline.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.ai.agent import get_agent_factory
from dogeapi.db import get_session
from dogeapi.deps import get_redis
from dogeapi.main import create_app
from dogeapi.settings import Settings, get_settings
from tests.conftest import TEST_DB_URL_ASYNC, TEST_DB_URL_SYNC, TEST_REDIS_URL

pytestmark = pytest.mark.integration

PASSWORD = "correct horse battery staple"


@pytest.fixture
async def ai_client(db_session: AsyncSession, redis_client: Redis) -> AsyncIterator[AsyncClient]:
    get_settings.cache_clear()
    get_agent_factory.cache_clear()
    settings = Settings(
        APP_ENV="test",
        JWT_SECRET_KEY="test-secret-please-do-not-use-in-prod-32-chars",
        DATABASE_URL=TEST_DB_URL_ASYNC,
        DATABASE_URL_SYNC=TEST_DB_URL_SYNC,
        REDIS_URL=TEST_REDIS_URL,
        FEATURE_AI_CHAT=True,
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
    get_agent_factory.cache_clear()


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


class TestThreads:
    async def test_create_list_get_delete(self, ai_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(ai_client)

        create = await ai_client.post(
            "/orgs/acme/ai/threads",
            json={"title": "First chat"},
            headers=owner,
        )
        assert create.status_code == 201
        thread = create.json()
        assert thread["title"] == "First chat"

        listed = await ai_client.get("/orgs/acme/ai/threads", headers=owner)
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        detail = await ai_client.get(f"/orgs/acme/ai/threads/{thread['id']}", headers=owner)
        assert detail.status_code == 200
        assert detail.json()["thread"]["id"] == thread["id"]
        assert detail.json()["messages"] == []

        deleted = await ai_client.delete(f"/orgs/acme/ai/threads/{thread['id']}", headers=owner)
        assert deleted.status_code == 204


class TestMessages:
    async def test_send_message_returns_assistant_response(self, ai_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(ai_client)
        thread = (await ai_client.post("/orgs/acme/ai/threads", json={"title": "T"}, headers=owner)).json()

        send = await ai_client.post(
            f"/orgs/acme/ai/threads/{thread['id']}/messages",
            json={"content": "Hello there"},
            headers=owner,
        )
        assert send.status_code == 200, send.text
        body = send.json()
        assert body["user_message"]["content"] == "Hello there"
        # Echo agent prefixes "echo: "
        assert body["assistant_message"]["content"].startswith("echo:")
        assert body["assistant_message"]["model"] == "echo"
        assert body["monthly_tokens_used"] >= 0

    async def test_messages_persist_across_requests(self, ai_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(ai_client)
        thread = (await ai_client.post("/orgs/acme/ai/threads", json={"title": "T"}, headers=owner)).json()
        await ai_client.post(
            f"/orgs/acme/ai/threads/{thread['id']}/messages",
            json={"content": "first"},
            headers=owner,
        )
        await ai_client.post(
            f"/orgs/acme/ai/threads/{thread['id']}/messages",
            json={"content": "second"},
            headers=owner,
        )
        detail = await ai_client.get(f"/orgs/acme/ai/threads/{thread['id']}", headers=owner)
        messages = detail.json()["messages"]
        assert len(messages) == 4
        assert [m["role"] for m in messages] == [
            "user",
            "assistant",
            "user",
            "assistant",
        ]


class TestQuota:
    async def test_blocks_when_quota_exceeded(self, ai_client: AsyncClient) -> None:
        """Free plan default monthly limit is 100k tokens; force a tiny limit
        through the redis counter to validate the guard fires."""
        from dogeapi.ai import quota

        owner = await _signup_owner_with_org(ai_client)
        thread = (await ai_client.post("/orgs/acme/ai/threads", json={"title": "T"}, headers=owner)).json()

        # Look up the org id to seed the counter near the cap
        orgs = await ai_client.get("/orgs", headers=owner)
        org_id = orgs.json()[0]["id"]

        from uuid import UUID

        from redis.asyncio import Redis as AsyncRedis

        client = AsyncRedis.from_url(TEST_REDIS_URL, decode_responses=False)
        await client.set(quota._key(UUID(org_id)), str(99_999_999))
        await client.aclose()

        send = await ai_client.post(
            f"/orgs/acme/ai/threads/{thread['id']}/messages",
            json={"content": "any"},
            headers=owner,
        )
        assert send.status_code == 429
