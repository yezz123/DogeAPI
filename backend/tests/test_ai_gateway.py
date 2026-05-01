"""Tests for the LLM Gateway integration (P10b).

We mock the gateway over HTTP with respx so the tests stay offline.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal

import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.ai import gateway
from dogeapi.db import get_session
from dogeapi.deps import get_redis
from dogeapi.main import create_app
from dogeapi.settings import Settings, get_settings
from tests.conftest import TEST_DB_URL_ASYNC, TEST_DB_URL_SYNC, TEST_REDIS_URL

pytestmark = pytest.mark.integration

PASSWORD = "correct horse battery staple"
GATEWAY_BASE = "https://api.llmgateway.io/v1"


@pytest.fixture
async def gateway_client(db_session: AsyncSession, redis_client: Redis) -> AsyncIterator[AsyncClient]:
    """Test client with FEATURE_AI_CHAT on AND a gateway key configured."""
    get_settings.cache_clear()
    settings = Settings(
        APP_ENV="test",
        JWT_SECRET_KEY="test-secret-please-do-not-use-in-prod-32-chars",
        DATABASE_URL=TEST_DB_URL_ASYNC,
        DATABASE_URL_SYNC=TEST_DB_URL_SYNC,
        REDIS_URL=TEST_REDIS_URL,
        FEATURE_AI_CHAT=True,
        LLM_GATEWAY_URL=GATEWAY_BASE,
        LLM_GATEWAY_API_KEY="test-key",
        AI_DEFAULT_MODEL="gpt-5-mini",
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


# ─── Models endpoint ─────────────────────────────────────────────────────


class TestModelsEndpoint:
    @respx.mock
    async def test_returns_filtered_model_list_from_gateway(self, gateway_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(gateway_client)
        respx.get(f"{GATEWAY_BASE}/models").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "gpt-5",
                            "name": "GPT-5",
                            "family": "openai",
                            "description": "gpt-5",
                            "context_length": 400_000,
                            "architecture": {
                                "input_modalities": ["text", "image"],
                                "output_modalities": ["text"],
                            },
                            "json_output": True,
                            "structured_outputs": True,
                            "free": False,
                        },
                        {
                            "id": "gpt-4o-mini",
                            "name": "GPT-4o Mini",
                            "family": "openai",
                            "description": "deprecated",
                            "context_length": 128_000,
                            "architecture": {
                                "input_modalities": ["text"],
                                "output_modalities": ["text"],
                            },
                            "json_output": True,
                            "structured_outputs": True,
                            "free": False,
                            "deprecated_at": "2026-01-09T00:00:00.000Z",
                        },
                    ]
                },
            )
        )

        response = await gateway_client.get("/orgs/acme/ai/models", headers=owner)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["configured"] is True
        assert body["default_model"] == "gpt-5-mini"
        ids = [m["id"] for m in body["models"]]
        assert "gpt-5" in ids
        # deprecated models are filtered out
        assert "gpt-4o-mini" not in ids

    async def test_returns_echo_placeholder_when_unconfigured(
        self, db_session: AsyncSession, redis_client: Redis
    ) -> None:
        get_settings.cache_clear()
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

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            owner = await _signup_owner_with_org(client)
            response = await client.get("/orgs/acme/ai/models", headers=owner)
            assert response.status_code == 200
            body = response.json()
            assert body["configured"] is False
            assert body["default_model"] == "echo"
            assert body["models"][0]["id"] == "echo"

        get_settings.cache_clear()


# ─── Chat completion ──────────────────────────────────────────────────────


class TestChatCompletionViaGateway:
    @respx.mock
    async def test_send_message_routes_to_gateway_and_records_cost(self, gateway_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(gateway_client)

        respx.post(f"{GATEWAY_BASE}/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "resp-1",
                    "object": "chat.completion",
                    "model": "gpt-5",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "hello from gpt-5",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 12,
                        "completion_tokens": 5,
                        "total_tokens": 17,
                        "cost": 0.000123,
                    },
                    "metadata": {
                        "request_id": "req-abc",
                        "used_provider": "openai",
                    },
                },
            )
        )

        thread = (
            await gateway_client.post(
                "/orgs/acme/ai/threads",
                json={"title": "T", "default_model": "gpt-5"},
                headers=owner,
            )
        ).json()

        send = await gateway_client.post(
            f"/orgs/acme/ai/threads/{thread['id']}/messages",
            json={"content": "Hi", "model": "gpt-5"},
            headers=owner,
        )
        assert send.status_code == 200, send.text
        body = send.json()
        assistant = body["assistant_message"]
        assert assistant["content"] == "hello from gpt-5"
        assert assistant["model"] == "gpt-5"
        assert assistant["tokens_in"] == 12
        assert assistant["tokens_out"] == 5
        assert Decimal(assistant["cost_usd"]) == Decimal("0.000123")
        assert assistant["extra"]["request_id"] == "req-abc"
        assert assistant["extra"]["used_provider"] == "openai"

    @respx.mock
    async def test_gateway_5xx_returns_502(self, gateway_client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(gateway_client)
        respx.post(f"{GATEWAY_BASE}/chat/completions").mock(return_value=httpx.Response(503, text="upstream down"))

        thread = (
            await gateway_client.post(
                "/orgs/acme/ai/threads",
                json={"title": "T", "default_model": "gpt-5"},
                headers=owner,
            )
        ).json()
        send = await gateway_client.post(
            f"/orgs/acme/ai/threads/{thread['id']}/messages",
            json={"content": "Hi"},
            headers=owner,
        )
        assert send.status_code == 502


# ─── Pure helper test (no app) ───────────────────────────────────────────


class TestGatewayHelpers:
    @respx.mock
    async def test_chat_completion_returns_normalised_result(self) -> None:
        respx.post(f"{GATEWAY_BASE}/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "gpt-5",
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 2,
                        "cost": 0.0005,
                    },
                },
            )
        )
        settings = Settings(
            JWT_SECRET_KEY="x",
            LLM_GATEWAY_URL=GATEWAY_BASE,
            LLM_GATEWAY_API_KEY="key",
        )
        result = await gateway.chat_completion(settings, model="gpt-5", messages=[{"role": "user", "content": "hi"}])
        assert result.text == "ok"
        assert result.tokens_in == 1
        assert result.tokens_out == 2
        assert result.cost_usd == Decimal("0.0005")
