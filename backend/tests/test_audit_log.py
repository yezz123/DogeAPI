"""Tests for the audit log module (P5).

Audit log writes happen on a side-channel session that bypasses the
test's SAVEPOINT, so each test in this file truncates the table before
running. The ``feature_flags(audit_log=True)`` marker enables the
middleware just for this file.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import TEST_DB_URL_ASYNC

pytestmark = [pytest.mark.integration, pytest.mark.feature_flags(audit_log=True)]

PASSWORD = "correct horse battery staple"


@pytest.fixture(autouse=True)
async def _truncate_audit_logs():
    """Each test starts with an empty audit_logs table."""
    engine = create_async_engine(TEST_DB_URL_ASYNC, future=True)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE audit_logs RESTART IDENTITY CASCADE"))
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE audit_logs RESTART IDENTITY CASCADE"))
    await engine.dispose()


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


class TestMiddlewareCaptures:
    async def test_post_org_invitations_logs_event(self, client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(client)

        invite = await client.post(
            "/orgs/acme/invitations",
            json={"email": "bob@example.com", "role": "member"},
            headers=owner,
        )
        assert invite.status_code == 201, invite.text

        # Wait nothing — middleware writes synchronously after call_next.
        listed = await client.get("/orgs/acme/audit-log", headers=owner)
        assert listed.status_code == 200
        actions = [row["action"] for row in listed.json()]
        assert any(a.startswith("invitation.") for a in actions)

    async def test_get_requests_are_not_logged(self, client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(client)
        await client.get("/orgs/acme/members", headers=owner)
        listed = await client.get("/orgs/acme/audit-log", headers=owner)
        actions = [row["action"] for row in listed.json()]
        assert not any(a == "member.read" for a in actions)

    async def test_failed_mutations_are_not_logged(self, client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(client)
        # Try to invite without scope: switch using a member-role peer
        invite = await client.post(
            "/orgs/acme/invitations",
            json={"email": "bob@example.com", "role": "member"},
            headers=owner,
        )
        token = invite.json()["invite_link"].split("token=", 1)[1]
        bob_signup = await client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": PASSWORD},
        )
        bob_headers = {"Authorization": f"Bearer {bob_signup.json()['tokens']['access_token']}"}
        await client.post("/invitations/accept", json={"token": token}, headers=bob_headers)
        switch = await client.post("/orgs/acme/switch", headers=bob_headers)
        bob_scoped = {"Authorization": f"Bearer {switch.json()['access_token']}"}

        before = await client.get("/orgs/acme/audit-log", headers=owner)
        before_count = len(before.json())

        forbidden = await client.post(
            "/orgs/acme/invitations",
            json={"email": "carol@example.com", "role": "member"},
            headers=bob_scoped,
        )
        assert forbidden.status_code == 403

        after = await client.get("/orgs/acme/audit-log", headers=owner)
        after_count = len(after.json())
        assert after_count == before_count


class TestEndpoint:
    async def test_member_role_cannot_read_audit_log(self, client: AsyncClient) -> None:
        owner = await _signup_owner_with_org(client)
        invite = await client.post(
            "/orgs/acme/invitations",
            json={"email": "bob@example.com", "role": "member"},
            headers=owner,
        )
        token = invite.json()["invite_link"].split("token=", 1)[1]
        bob = await client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": PASSWORD},
        )
        bh = {"Authorization": f"Bearer {bob.json()['tokens']['access_token']}"}
        await client.post("/invitations/accept", json={"token": token}, headers=bh)
        switch = await client.post("/orgs/acme/switch", headers=bh)
        bob_scoped = {"Authorization": f"Bearer {switch.json()['access_token']}"}

        response = await client.get("/orgs/acme/audit-log", headers=bob_scoped)
        assert response.status_code == 403
