"""Role &rarr; scope mapping.

Scopes use ``namespace:resource:action`` notation; authx supports wildcard
matching (``"org:*"`` covers everything beneath ``org:``). The scopes are
embedded in the access token at issue-time; ``auth.scopes_required(...)``
enforces them on individual routes.
"""

from __future__ import annotations

from collections.abc import Iterable

from dogeapi.models import Role

ROLE_SCOPES: dict[Role, list[str]] = {
    Role.OWNER: [
        "org:*",
    ],
    Role.ADMIN: [
        "org:read",
        "org:members:read",
        "org:members:write",
        "org:invitations:*",
        "org:apikeys:*",
        "org:audit:read",
        "org:billing:read",
        "org:ai:*",
    ],
    Role.MEMBER: [
        "org:read",
        "org:members:read",
        "org:ai:use",
    ],
}


def scopes_for_role(role: Role) -> list[str]:
    """Return the scope list for a given role, copying so callers can mutate."""
    return list(ROLE_SCOPES[role])


def role_max_among(roles: Iterable[Role]) -> Role:
    """Return the highest-rank role from an iterable, defaulting to MEMBER."""
    best = Role.MEMBER
    for role in roles:
        if role.rank > best.rank:
            best = role
    return best
