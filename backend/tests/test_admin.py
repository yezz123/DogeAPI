"""Tests for super-admin endpoints (P12)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.models import User

pytestmark = pytest.mark.integration

PASSWORD = "correct horse battery staple"


async def _signup(client: AsyncClient, email: str) -> dict[str, str]:
    r = await client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    body = r.json()
    return {"Authorization": f"Bearer {body['tokens']['access_token']}"}


async def _make_superadmin(session: AsyncSession, email: str) -> None:
    from sqlalchemy import select

    stmt = select(User).where(User.email == email)
    user = (await session.execute(stmt)).scalar_one()
    user.is_superadmin = True
    await session.flush()


class TestAuthorization:
    async def test_non_superadmin_gets_403(self, client: AsyncClient) -> None:
        regular = await _signup(client, "regular@example.com")
        response = await client.get("/admin/tenants", headers=regular)
        assert response.status_code == 403

    async def test_unauthenticated_gets_401(self, client: AsyncClient) -> None:
        response = await client.get("/admin/tenants")
        assert response.status_code == 401


class TestTenants:
    async def test_lists_tenants_for_superadmin(self, client: AsyncClient, db_session: AsyncSession) -> None:
        owner = await _signup(client, "owner@example.com")
        await client.post("/orgs", json={"name": "Acme", "slug": "acme"}, headers=owner)

        admin = await _signup(client, "admin@example.com")
        await _make_superadmin(db_session, "admin@example.com")

        response = await client.get("/admin/tenants", headers=admin)
        assert response.status_code == 200
        body = response.json()
        slugs = [t["slug"] for t in body]
        assert "acme" in slugs

    async def test_get_tenant_404_for_unknown(self, client: AsyncClient, db_session: AsyncSession) -> None:
        admin = await _signup(client, "admin@example.com")
        await _make_superadmin(db_session, "admin@example.com")

        from uuid import uuid4

        response = await client.get(f"/admin/tenants/{uuid4()}", headers=admin)
        assert response.status_code == 404


class TestUsers:
    async def test_lists_and_filters_by_email(self, client: AsyncClient, db_session: AsyncSession) -> None:
        await _signup(client, "alice@example.com")
        await _signup(client, "bob@example.com")
        admin = await _signup(client, "admin@example.com")
        await _make_superadmin(db_session, "admin@example.com")

        listed = await client.get("/admin/users", headers=admin)
        assert listed.status_code == 200
        emails = [u["email"] for u in listed.json()]
        assert "alice@example.com" in emails

        filtered = await client.get("/admin/users?email=bob", headers=admin)
        assert filtered.status_code == 200
        assert all("bob" in u["email"] for u in filtered.json())


class TestSystemHealth:
    async def test_returns_db_and_redis_status(self, client: AsyncClient, db_session: AsyncSession) -> None:
        admin = await _signup(client, "admin@example.com")
        await _make_superadmin(db_session, "admin@example.com")

        response = await client.get("/admin/system-health", headers=admin)
        assert response.status_code == 200
        body = response.json()
        assert body["db_ok"] is True
        assert body["redis_ok"] is True
        assert body["total_users"] >= 1
