"""Business logic for orgs / memberships / invitations.

All write functions take a session and return ORM instances. Errors are
domain-typed exceptions so the router can map them onto HTTP status codes.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.models import Invitation, Membership, Organization, Role, User

INVITATION_TTL = timedelta(days=7)


# ─── Errors ───────────────────────────────────────────────────────────────


class OrganizationNotFoundError(Exception):
    pass


class SlugTakenError(Exception):
    pass


class NotAMemberError(Exception):
    pass


class InsufficientPermissionError(Exception):
    pass


class InvitationNotFoundError(Exception):
    pass


class AlreadyMemberError(Exception):
    pass


class CannotRemoveLastOwnerError(Exception):
    pass


# ─── Slug helpers ─────────────────────────────────────────────────────────


_SLUG_BAD = re.compile(r"[^a-z0-9-]+")


def slugify(name: str) -> str:
    base = _SLUG_BAD.sub("-", name.strip().lower()).strip("-")
    return base or "org"


async def _slug_is_taken(session: AsyncSession, slug: str) -> bool:
    result = await session.execute(select(Organization.id).where(Organization.slug == slug))
    return result.scalar_one_or_none() is not None


async def _generate_unique_slug(session: AsyncSession, name: str) -> str:
    base = slugify(name)
    if not await _slug_is_taken(session, base):
        return base
    for n in range(2, 1000):
        candidate = f"{base}-{n}"
        if not await _slug_is_taken(session, candidate):
            return candidate
    return f"{base}-{secrets.token_hex(4)}"


# ─── Organizations ────────────────────────────────────────────────────────


async def create_organization(
    session: AsyncSession,
    *,
    owner: User,
    name: str,
    slug: str | None = None,
) -> tuple[Organization, Membership]:
    """Create an org and seed an OWNER membership for the caller."""
    chosen_slug = slug or await _generate_unique_slug(session, name)
    if slug and await _slug_is_taken(session, chosen_slug):
        raise SlugTakenError(chosen_slug)

    org = Organization(slug=chosen_slug, name=name)
    session.add(org)
    await session.flush()

    membership = Membership(user_id=owner.id, org_id=org.id, role=Role.OWNER)
    session.add(membership)
    await session.flush()
    return org, membership


async def get_organization_by_slug(session: AsyncSession, slug: str) -> Organization | None:
    result = await session.execute(select(Organization).where(Organization.slug == slug))
    return result.scalar_one_or_none()


async def list_user_organizations(
    session: AsyncSession,
    user_id: UUID,
) -> list[tuple[Organization, Role]]:
    stmt = (
        select(Organization, Membership.role)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == user_id)
        .order_by(Organization.created_at)
    )
    result = await session.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]


async def get_membership(
    session: AsyncSession,
    *,
    user_id: UUID,
    org_id: UUID,
) -> Membership | None:
    stmt = select(Membership).where(and_(Membership.user_id == user_id, Membership.org_id == org_id))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_members(session: AsyncSession, org_id: UUID) -> list[tuple[User, Membership]]:
    stmt = (
        select(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.org_id == org_id)
        .order_by(Membership.created_at)
    )
    result = await session.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]


async def change_role(
    session: AsyncSession,
    *,
    org_id: UUID,
    target_user_id: UUID,
    new_role: Role,
) -> Membership:
    membership = await get_membership(session, user_id=target_user_id, org_id=org_id)
    if membership is None:
        raise NotAMemberError

    if membership.role is Role.OWNER and new_role is not Role.OWNER and await _count_owners(session, org_id) <= 1:
        raise CannotRemoveLastOwnerError

    membership.role = new_role
    await session.flush()
    return membership


async def remove_member(session: AsyncSession, *, org_id: UUID, target_user_id: UUID) -> None:
    membership = await get_membership(session, user_id=target_user_id, org_id=org_id)
    if membership is None:
        raise NotAMemberError
    if membership.role is Role.OWNER and await _count_owners(session, org_id) <= 1:
        raise CannotRemoveLastOwnerError
    await session.delete(membership)
    await session.flush()


async def _count_owners(session: AsyncSession, org_id: UUID) -> int:
    stmt = select(Membership).where(and_(Membership.org_id == org_id, Membership.role == Role.OWNER))
    result = await session.execute(stmt)
    return len(result.scalars().all())


# ─── Invitations ──────────────────────────────────────────────────────────


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_invitation(
    session: AsyncSession,
    *,
    org: Organization,
    email: str,
    role: Role,
    invited_by: User,
) -> tuple[Invitation, str]:
    """Create an invite and return it together with the *plaintext* token.

    The plaintext token is what we send / surface to the user; only the
    hash is persisted.
    """
    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        org_id=org.id,
        email=email,
        role=role,
        token_hash=_hash_token(token),
        invited_by_id=invited_by.id,
        expires_at=datetime.now(UTC) + INVITATION_TTL,
    )
    session.add(invitation)
    await session.flush()
    return invitation, token


async def list_invitations(
    session: AsyncSession,
    org_id: UUID,
    *,
    only_pending: bool = True,
) -> list[Invitation]:
    stmt = select(Invitation).where(Invitation.org_id == org_id)
    if only_pending:
        stmt = stmt.where(Invitation.accepted_at.is_(None))
    stmt = stmt.order_by(Invitation.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def revoke_invitation(session: AsyncSession, *, org_id: UUID, invitation_id: UUID) -> None:
    inv = await session.get(Invitation, invitation_id)
    if inv is None or inv.org_id != org_id:
        raise InvitationNotFoundError(str(invitation_id))
    await session.delete(inv)
    await session.flush()


async def accept_invitation(
    session: AsyncSession,
    *,
    token: str,
    user: User,
) -> Membership:
    """Validate the token, attach the user to the org, return their membership."""
    stmt = select(Invitation).where(Invitation.token_hash == _hash_token(token))
    result = await session.execute(stmt)
    invitation = result.scalar_one_or_none()
    if invitation is None or invitation.accepted_at is not None:
        raise InvitationNotFoundError("invalid or already-used token")
    if invitation.expires_at < datetime.now(UTC):
        raise InvitationNotFoundError("expired")

    existing = await get_membership(session, user_id=user.id, org_id=invitation.org_id)
    if existing is not None:
        invitation.accepted_at = datetime.now(UTC)
        invitation.accepted_by_id = user.id
        await session.flush()
        raise AlreadyMemberError(str(invitation.org_id))

    membership = Membership(user_id=user.id, org_id=invitation.org_id, role=invitation.role)
    session.add(membership)
    invitation.accepted_at = datetime.now(UTC)
    invitation.accepted_by_id = user.id
    await session.flush()
    return membership
