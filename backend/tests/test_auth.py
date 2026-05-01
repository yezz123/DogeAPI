"""Tests for the auth module (P1).

Covers register / login / refresh / logout / me / verify-email.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

EMAIL = "alice@example.com"
PASSWORD = "correct horse battery staple"


async def _register(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD) -> dict[str, Any]:
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Alice"},
    )
    assert response.status_code == 201, response.text
    return response.json()


class TestRegister:
    async def test_creates_user_and_returns_201(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/register",
            json={"email": EMAIL, "password": PASSWORD},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["user"]["email"] == EMAIL
        assert body["user"]["email_verified_at"] is None
        assert body["tokens"]["access_token"]
        assert body["tokens"]["refresh_token"]

    async def test_returns_email_verification_link_when_delivery_disabled(self, client: AsyncClient) -> None:
        body = await _register(client)
        assert body["email_verification_link"]
        assert "/verify-email?token=" in body["email_verification_link"]

    async def test_409_on_duplicate_email(self, client: AsyncClient) -> None:
        await _register(client)
        response = await client.post(
            "/auth/register",
            json={"email": EMAIL, "password": PASSWORD},
        )
        assert response.status_code == 409

    async def test_422_on_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/register",
            json={"email": EMAIL, "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:
    async def test_returns_token_pair_on_valid_credentials(self, client: AsyncClient) -> None:
        await _register(client)
        response = await client.post(
            "/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"

    async def test_401_on_wrong_password(self, client: AsyncClient) -> None:
        await _register(client)
        response = await client.post(
            "/auth/login",
            json={"email": EMAIL, "password": "wrong-password"},
        )
        assert response.status_code == 401

    async def test_401_on_unknown_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/auth/login",
            json={"email": "ghost@example.com", "password": PASSWORD},
        )
        assert response.status_code == 401


class TestMe:
    async def test_returns_current_user_for_valid_token(self, client: AsyncClient) -> None:
        body = await _register(client)
        access = body["tokens"]["access_token"]
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert response.status_code == 200
        assert response.json()["email"] == EMAIL

    async def test_401_without_token(self, client: AsyncClient) -> None:
        response = await client.get("/auth/me")
        assert response.status_code == 401


class TestRefresh:
    async def test_exchanges_refresh_token_for_new_pair(self, client: AsyncClient) -> None:
        body = await _register(client)
        refresh_token = body["tokens"]["refresh_token"]

        response = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
        assert response.status_code == 200
        new_body = response.json()
        assert new_body["access_token"]
        assert new_body["refresh_token"]

    async def test_rejects_access_token_used_as_refresh(self, client: AsyncClient) -> None:
        body = await _register(client)
        access = body["tokens"]["access_token"]
        response = await client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert response.status_code in {401, 403}


class TestLogout:
    async def test_blocklists_token_so_it_cannot_be_reused(self, client: AsyncClient) -> None:
        body = await _register(client)
        access = body["tokens"]["access_token"]

        logout = await client.post("/auth/logout", headers={"Authorization": f"Bearer {access}"})
        assert logout.status_code == 200

        replay = await client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert replay.status_code in {401, 403}


class TestVerifyEmail:
    async def test_marks_email_verified(self, client: AsyncClient) -> None:
        body = await _register(client)
        link = body["email_verification_link"]
        token = link.split("token=", 1)[1]

        response = await client.post("/auth/verify-email", json={"token": token})
        assert response.status_code == 200

        access = body["tokens"]["access_token"]
        me = await client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
        assert me.json()["email_verified_at"] is not None

    async def test_400_on_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post("/auth/verify-email", json={"token": "not-a-real-token"})
        assert response.status_code == 400

    async def test_400_on_replay(self, client: AsyncClient) -> None:
        body = await _register(client)
        token = body["email_verification_link"].split("token=", 1)[1]

        first = await client.post("/auth/verify-email", json={"token": token})
        assert first.status_code == 200

        second = await client.post("/auth/verify-email", json={"token": token})
        assert second.status_code == 400
