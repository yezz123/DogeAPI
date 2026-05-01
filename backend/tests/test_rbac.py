"""Exhaustive role x route denial matrix for org-scoped endpoints (P3).

For each role we set up a user and switch them into the org, then assert
which endpoints the role can / cannot reach. This is the safety net that
makes refactoring scopes safe.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

PASSWORD = "correct horse battery staple"


async def _signup(client: AsyncClient, email: str) -> dict[str, Any]:
    r = await client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return {
        "user": body["user"],
        "headers": {"Authorization": f"Bearer {body['tokens']['access_token']}"},
    }


async def _switch(client: AsyncClient, headers: dict[str, str], slug: str) -> dict[str, str]:
    r = await client.post(f"/orgs/{slug}/switch", headers=headers)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
async def role_setup(client: AsyncClient) -> dict[str, dict[str, Any]]:
    """Build an org with one of each role.

    Returns ``{"owner": {...}, "admin": {...}, "member": {...}, "outsider": {...}}``
    where each value has ``user`` and ``headers`` keys, with ``headers``
    scoped to the org (except for outsider, who has a non-scoped JWT).
    """
    owner = await _signup(client, "owner@example.com")
    org_resp = await client.post("/orgs", json={"name": "Acme", "slug": "acme"}, headers=owner["headers"])
    assert org_resp.status_code == 201
    owner["headers"] = await _switch(client, owner["headers"], "acme")

    async def _make(role: str, email: str) -> dict[str, Any]:
        invite = await client.post(
            "/orgs/acme/invitations",
            json={"email": email, "role": role},
            headers=owner["headers"],
        )
        token = invite.json()["invite_link"].split("token=", 1)[1]
        invitee = await _signup(client, email)
        await client.post(
            "/invitations/accept",
            json={"token": token},
            headers=invitee["headers"],
        )
        invitee["headers"] = await _switch(client, invitee["headers"], "acme")
        return invitee

    admin = await _make("admin", "admin@example.com")
    member = await _make("member", "member@example.com")
    outsider = await _signup(client, "outsider@example.com")

    return {"owner": owner, "admin": admin, "member": member, "outsider": outsider}


# ─── Read access ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("role", ["owner", "admin", "member"])
async def test_org_read_allowed_for_all_members(
    client: AsyncClient,
    role_setup: dict[str, dict[str, Any]],
    role: str,
) -> None:
    actor = role_setup[role]
    response = await client.get("/orgs/acme", headers=actor["headers"])
    assert response.status_code == 200, f"role={role}: {response.text}"


async def test_org_read_denied_for_outsider(client: AsyncClient, role_setup: dict[str, dict[str, Any]]) -> None:
    response = await client.get("/orgs/acme", headers=role_setup["outsider"]["headers"])
    assert response.status_code == 403


# ─── Members listing ──────────────────────────────────────────────────────


@pytest.mark.parametrize("role", ["owner", "admin", "member"])
async def test_members_list_allowed_for_all_members(
    client: AsyncClient,
    role_setup: dict[str, dict[str, Any]],
    role: str,
) -> None:
    response = await client.get("/orgs/acme/members", headers=role_setup[role]["headers"])
    assert response.status_code == 200


# ─── Members write (change role / remove) ─────────────────────────────────


@pytest.mark.parametrize(
    ("actor_role", "expected"),
    [
        ("owner", 200),
        ("admin", 200),
        ("member", 403),
    ],
)
async def test_change_member_role(
    client: AsyncClient,
    role_setup: dict[str, dict[str, Any]],
    actor_role: str,
    expected: int,
) -> None:
    target_id = role_setup["member"]["user"]["id"]
    response = await client.patch(
        f"/orgs/acme/members/{target_id}",
        json={"role": "admin"},
        headers=role_setup[actor_role]["headers"],
    )
    assert response.status_code == expected, response.text


@pytest.mark.parametrize(
    ("actor_role", "expected"),
    [
        ("owner", 204),
        ("admin", 204),
        ("member", 403),
    ],
)
async def test_remove_member(
    client: AsyncClient,
    role_setup: dict[str, dict[str, Any]],
    actor_role: str,
    expected: int,
) -> None:
    target_id = role_setup["member"]["user"]["id"]
    response = await client.delete(
        f"/orgs/acme/members/{target_id}",
        headers=role_setup[actor_role]["headers"],
    )
    assert response.status_code == expected


# ─── Invitations ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("actor_role", "expected_create"),
    [
        ("owner", 201),
        ("admin", 201),
        ("member", 403),
    ],
)
async def test_create_invitation(
    client: AsyncClient,
    role_setup: dict[str, dict[str, Any]],
    actor_role: str,
    expected_create: int,
) -> None:
    response = await client.post(
        "/orgs/acme/invitations",
        json={"email": f"new-{actor_role}@example.com", "role": "member"},
        headers=role_setup[actor_role]["headers"],
    )
    assert response.status_code == expected_create


@pytest.mark.parametrize(
    ("actor_role", "expected"),
    [
        ("owner", 200),
        ("admin", 200),
        ("member", 403),
    ],
)
async def test_list_invitations(
    client: AsyncClient,
    role_setup: dict[str, dict[str, Any]],
    actor_role: str,
    expected: int,
) -> None:
    response = await client.get(
        "/orgs/acme/invitations",
        headers=role_setup[actor_role]["headers"],
    )
    assert response.status_code == expected


# ─── Cross-org isolation ──────────────────────────────────────────────────


async def test_token_for_one_org_cannot_access_another(client: AsyncClient) -> None:
    """A JWT scoped to org A must not work against org B's URL."""
    alice = await _signup(client, "alice@example.com")
    await client.post("/orgs", json={"name": "Acme", "slug": "acme"}, headers=alice["headers"])
    await client.post("/orgs", json={"name": "Beta", "slug": "beta"}, headers=alice["headers"])
    acme_headers = await _switch(client, alice["headers"], "acme")

    response = await client.get("/orgs/beta/members", headers=acme_headers)
    assert response.status_code == 403


# ─── Self-leave doesn't need org:members:write ────────────────────────────


async def test_member_can_leave_own_org_without_write_scope(
    client: AsyncClient, role_setup: dict[str, dict[str, Any]]
) -> None:
    response = await client.post("/orgs/acme/leave", headers=role_setup["member"]["headers"])
    assert response.status_code == 204


# ─── Update org ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("actor_role", "expected"),
    [
        ("owner", 200),
        ("admin", 403),
        ("member", 403),
    ],
)
async def test_update_org(
    client: AsyncClient,
    role_setup: dict[str, dict[str, Any]],
    actor_role: str,
    expected: int,
) -> None:
    """Only OWNERs have ``org:write``."""
    response = await client.patch(
        "/orgs/acme",
        json={"name": "Acme Renamed"},
        headers=role_setup[actor_role]["headers"],
    )
    assert response.status_code == expected
