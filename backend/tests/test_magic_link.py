"""Tests for the magic-link module (P7)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.feature_flags(magic_link=True)]


class TestRequest:
    async def test_returns_link_when_email_disabled_and_user_exists(self, client: AsyncClient) -> None:
        # Pre-register a user
        await client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "correct horse battery staple"},
        )

        response = await client.post(
            "/auth/magic-link/request",
            json={"email": "alice@example.com"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["link"] is not None
        assert "/magic-link?token=" in body["link"]

    async def test_unknown_email_returns_success_without_link(self, client: AsyncClient) -> None:
        """Don't leak which emails are registered."""
        response = await client.post(
            "/auth/magic-link/request",
            json={"email": "ghost@example.com"},
        )
        assert response.status_code == 200
        assert response.json()["link"] is None


class TestConsume:
    async def test_consumes_token_and_returns_jwt(self, client: AsyncClient) -> None:
        await client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "correct horse battery staple"},
        )

        request = await client.post(
            "/auth/magic-link/request",
            json={"email": "alice@example.com"},
        )
        token = request.json()["link"].split("token=", 1)[1]

        consume = await client.post(
            "/auth/magic-link/consume",
            json={"token": token},
        )
        assert consume.status_code == 200
        body = consume.json()
        assert body["user"]["email"] == "alice@example.com"
        assert body["user"]["email_verified_at"] is not None
        assert body["tokens"]["access_token"]

    async def test_replay_returns_400(self, client: AsyncClient) -> None:
        await client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "correct horse battery staple"},
        )
        request = await client.post(
            "/auth/magic-link/request",
            json={"email": "alice@example.com"},
        )
        token = request.json()["link"].split("token=", 1)[1]

        first = await client.post("/auth/magic-link/consume", json={"token": token})
        assert first.status_code == 200

        replay = await client.post("/auth/magic-link/consume", json={"token": token})
        assert replay.status_code == 400

    async def test_creates_user_on_first_link_consumption(self, client: AsyncClient) -> None:
        """A magic-link to an unknown email creates a passwordless user."""
        # We bypass the request privacy filter by issuing a token directly.
        from datetime import timedelta

        from dogeapi.magic_link import service

        redis = (await client.get("/healthz")).headers  # touch the client
        del redis  # silencing unused

        # Issue token directly via the redis client used by the test fixture
        # — easier than pre-registering then deleting.
        # The conftest's redis_client fixture is the one wired into the app.
        from redis.asyncio import Redis

        rclient = Redis.from_url("redis://localhost:6379/15", decode_responses=False)
        token = await service.issue(rclient, "newbie@example.com", ttl=timedelta(minutes=5))
        await rclient.aclose()

        response = await client.post("/auth/magic-link/consume", json={"token": token})
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "newbie@example.com"
