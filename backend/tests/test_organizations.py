"""Tests for the organizations module (P2 + P3 RBAC).

Covers:
- create / list / get / update orgs
- switch-org and JWT re-issue with org_id + role + scopes
- members CRUD with last-owner protection
- invitations create / list / accept / revoke
- self-leave endpoint
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


# ─── Helpers ──────────────────────────────────────────────────────────────


async def _signup(
    client: AsyncClient,
    email: str = "alice@example.com",
    password: str = "correct horse battery staple",
    full_name: str | None = "Alice",
) -> dict[str, Any]:
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return {
        "user": body["user"],
        "access_token": body["tokens"]["access_token"],
        "headers": {"Authorization": f"Bearer {body['tokens']['access_token']}"},
    }


async def _create_org(
    client: AsyncClient, headers: dict[str, str], *, name: str = "Acme Inc.", slug: str | None = None
) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name}
    if slug:
        body["slug"] = slug
    response = await client.post("/orgs", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def _switch_into(client: AsyncClient, headers: dict[str, str], slug: str) -> dict[str, str]:
    """Switch into the given org and return new auth headers."""
    response = await client.post(f"/orgs/{slug}/switch", headers=headers)
    assert response.status_code == 200, response.text
    access = response.json()["access_token"]
    return {"Authorization": f"Bearer {access}"}


async def _create_and_switch(
    client: AsyncClient, headers: dict[str, str], *, name: str, slug: str
) -> tuple[dict[str, Any], dict[str, str]]:
    """Create an org, switch into it, return (org_dict, scoped_headers)."""
    org = await _create_org(client, headers, name=name, slug=slug)
    new_headers = await _switch_into(client, headers, slug)
    return org, new_headers


async def _accept_invite_as(
    client: AsyncClient,
    *,
    email: str,
    org_slug: str,
    inviter_headers: dict[str, str],
    role: str = "member",
) -> dict[str, Any]:
    """Invite, register the invitee, accept, switch them in."""
    invite = await client.post(
        f"/orgs/{org_slug}/invitations",
        json={"email": email, "role": role},
        headers=inviter_headers,
    )
    assert invite.status_code == 201, invite.text
    token = invite.json()["invite_link"].split("token=", 1)[1]

    invitee = await _signup(client, email=email)
    accept = await client.post("/invitations/accept", json={"token": token}, headers=invitee["headers"])
    assert accept.status_code == 200, accept.text
    invitee["headers"] = await _switch_into(client, invitee["headers"], org_slug)
    return invitee


# ─── Tests ────────────────────────────────────────────────────────────────


class TestCreateOrg:
    async def test_creates_org_and_makes_caller_owner(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        org = await _create_org(client, alice["headers"], name="Acme")
        assert org["name"] == "Acme"
        assert org["slug"] == "acme"

        listed = await client.get("/orgs", headers=alice["headers"])
        items = listed.json()
        assert len(items) == 1
        assert items[0]["slug"] == "acme"
        assert items[0]["role"] == "owner"

    async def test_auto_unique_slug_on_collision(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        first = await _create_org(client, alice["headers"], name="Acme")
        second = await _create_org(client, alice["headers"], name="Acme")
        assert first["slug"] == "acme"
        assert second["slug"] == "acme-2"

    async def test_explicit_slug_collides_returns_409(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        await _create_org(client, alice["headers"], name="Acme", slug="acme")
        response = await client.post(
            "/orgs",
            json={"name": "Different", "slug": "acme"},
            headers=alice["headers"],
        )
        assert response.status_code == 409


class TestSwitchOrg:
    async def test_re_issues_token_with_org_id_and_role_and_scopes(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        await _create_org(client, alice["headers"], name="Acme", slug="acme")
        switch = await client.post("/orgs/acme/switch", headers=alice["headers"])
        assert switch.status_code == 200

        from authx import TokenPayload

        new_access = switch.json()["access_token"]
        payload = TokenPayload.decode(
            new_access,
            key="test-secret-please-do-not-use-in-prod-32-chars",
            algorithms=["HS256"],
        )
        extras = payload.model_extra or {}
        assert extras.get("role") == "owner"
        assert extras.get("org_id")
        assert payload.scopes is not None
        assert "org:*" in payload.scopes

    async def test_404_for_unknown_org(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        response = await client.post("/orgs/nope/switch", headers=alice["headers"])
        assert response.status_code == 404

    async def test_403_when_not_a_member(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        await _create_org(client, alice["headers"], name="Acme", slug="acme")
        bob = await _signup(client, email="bob@example.com")
        response = await client.post("/orgs/acme/switch", headers=bob["headers"])
        assert response.status_code == 403


class TestInviteFlow:
    async def test_owner_invites_user_who_can_then_accept(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        _, alice_scoped = await _create_and_switch(client, alice["headers"], name="Acme", slug="acme")

        invite = await client.post(
            "/orgs/acme/invitations",
            json={"email": "bob@example.com", "role": "member"},
            headers=alice_scoped,
        )
        assert invite.status_code == 201
        link = invite.json()["invite_link"]
        assert link
        token = link.split("token=", 1)[1]

        bob = await _signup(client, email="bob@example.com")
        accept = await client.post(
            "/invitations/accept",
            json={"token": token},
            headers=bob["headers"],
        )
        assert accept.status_code == 200
        assert accept.json()["role"] == "member"

        bob_scoped = await _switch_into(client, bob["headers"], "acme")
        listed = await client.get("/orgs/acme/members", headers=bob_scoped)
        assert listed.status_code == 200

    async def test_member_cannot_invite(self, client: AsyncClient) -> None:
        owner = await _signup(client, email="owner@example.com")
        _, owner_scoped = await _create_and_switch(client, owner["headers"], name="Acme", slug="acme")
        carol = await _accept_invite_as(
            client,
            email="carol@example.com",
            org_slug="acme",
            inviter_headers=owner_scoped,
            role="member",
        )
        forbidden = await client.post(
            "/orgs/acme/invitations",
            json={"email": "dave@example.com", "role": "member"},
            headers=carol["headers"],
        )
        assert forbidden.status_code == 403

    async def test_replay_invite_token_returns_400(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        _, alice_scoped = await _create_and_switch(client, alice["headers"], name="Acme", slug="acme")
        invite = await client.post(
            "/orgs/acme/invitations",
            json={"email": "bob@example.com", "role": "admin"},
            headers=alice_scoped,
        )
        token = invite.json()["invite_link"].split("token=", 1)[1]

        bob = await _signup(client, email="bob@example.com")
        first = await client.post("/invitations/accept", json={"token": token}, headers=bob["headers"])
        assert first.status_code == 200
        replay = await client.post("/invitations/accept", json={"token": token}, headers=bob["headers"])
        assert replay.status_code == 400


class TestMembers:
    async def test_owner_can_change_member_role(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        _, alice_scoped = await _create_and_switch(client, alice["headers"], name="Acme", slug="acme")
        bob = await _accept_invite_as(
            client,
            email="bob@example.com",
            org_slug="acme",
            inviter_headers=alice_scoped,
            role="member",
        )
        promote = await client.patch(
            f"/orgs/acme/members/{bob['user']['id']}",
            json={"role": "admin"},
            headers=alice_scoped,
        )
        assert promote.status_code == 200
        assert promote.json()["role"] == "admin"

    async def test_cannot_demote_last_owner(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        _, alice_scoped = await _create_and_switch(client, alice["headers"], name="Acme", slug="acme")
        response = await client.patch(
            f"/orgs/acme/members/{alice['user']['id']}",
            json={"role": "member"},
            headers=alice_scoped,
        )
        assert response.status_code == 400

    async def test_member_can_self_leave(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        _, alice_scoped = await _create_and_switch(client, alice["headers"], name="Acme", slug="acme")
        bob = await _accept_invite_as(
            client,
            email="bob@example.com",
            org_slug="acme",
            inviter_headers=alice_scoped,
            role="member",
        )
        leave = await client.post("/orgs/acme/leave", headers=bob["headers"])
        assert leave.status_code == 204

        # Bob's old token still has org_id, but membership is gone.
        # Re-switch should now 403.
        re_switch = await client.post("/orgs/acme/switch", headers=bob["headers"])
        assert re_switch.status_code == 403


class TestInvitationListAndRevoke:
    async def test_owner_can_list_and_revoke_pending_invites(self, client: AsyncClient) -> None:
        alice = await _signup(client)
        _, alice_scoped = await _create_and_switch(client, alice["headers"], name="Acme", slug="acme")
        invite = await client.post(
            "/orgs/acme/invitations",
            json={"email": "bob@example.com", "role": "member"},
            headers=alice_scoped,
        )
        invitation_id = invite.json()["invitation"]["id"]
        listed = await client.get("/orgs/acme/invitations", headers=alice_scoped)
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        revoke = await client.delete(
            f"/orgs/acme/invitations/{invitation_id}",
            headers=alice_scoped,
        )
        assert revoke.status_code == 204

        listed2 = await client.get("/orgs/acme/invitations", headers=alice_scoped)
        assert listed2.json() == []
