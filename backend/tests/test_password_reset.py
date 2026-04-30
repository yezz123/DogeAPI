"""Password reset tests (P8)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

PASSWORD = "correct horse battery staple"


class TestRequestReset:
    async def test_returns_link_when_email_disabled_for_known_user(self, client: AsyncClient) -> None:
        await client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": PASSWORD},
        )
        response = await client.post(
            "/auth/password-reset/request",
            json={"email": "alice@example.com"},
        )
        assert response.status_code == 200
        assert response.json()["link"] is not None

    async def test_unknown_email_returns_success_without_link(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/password-reset/request",
            json={"email": "ghost@example.com"},
        )
        assert response.status_code == 200
        assert response.json()["link"] is None


class TestConsumeReset:
    async def test_consumes_token_and_updates_password(self, client: AsyncClient) -> None:
        await client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": PASSWORD},
        )
        request = await client.post(
            "/auth/password-reset/request",
            json={"email": "alice@example.com"},
        )
        token = request.json()["link"].split("token=", 1)[1]

        new_password = "another correct horse battery staple"
        consume = await client.post(
            "/auth/password-reset/consume",
            json={"token": token, "new_password": new_password},
        )
        assert consume.status_code == 200

        # Old password no longer works
        old_login = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": PASSWORD},
        )
        assert old_login.status_code == 401

        # New password works
        new_login = await client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": new_password},
        )
        assert new_login.status_code == 200

    async def test_replay_returns_400(self, client: AsyncClient) -> None:
        await client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": PASSWORD},
        )
        request = await client.post(
            "/auth/password-reset/request",
            json={"email": "alice@example.com"},
        )
        token = request.json()["link"].split("token=", 1)[1]

        first = await client.post(
            "/auth/password-reset/consume",
            json={"token": token, "new_password": "another correct horse battery staple"},
        )
        assert first.status_code == 200

        replay = await client.post(
            "/auth/password-reset/consume",
            json={"token": token, "new_password": "another correct horse battery staple"},
        )
        assert replay.status_code == 400
