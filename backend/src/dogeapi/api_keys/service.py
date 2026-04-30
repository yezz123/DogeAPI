"""Business logic for API keys.

Key format: ``doge_{prefix}_{secret}`` where ``prefix`` is 8 url-safe chars
and ``secret`` is 32 url-safe chars. The hash stored is SHA-256 over the
*entire* key string (prefix included) so a stolen prefix alone is useless.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.models import APIKey, User

KEY_BRAND = "doge"


class APIKeyNotFoundError(Exception):
    pass


class ScopeNotPermittedError(Exception):
    """Raised when a creator tries to grant a scope they don't have."""


def _generate_key() -> tuple[str, str, str]:
    """Generate ``(plaintext, prefix, key_hash)``."""
    prefix = secrets.token_urlsafe(6)[:8]
    secret = secrets.token_urlsafe(32)
    plaintext = f"{KEY_BRAND}_{prefix}_{secret}"
    key_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    return plaintext, prefix, key_hash


def parse_key(plaintext: str) -> tuple[str, str] | None:
    """Return ``(prefix, key_hash)`` if the format looks right, else ``None``."""
    parts = plaintext.split("_", 2)
    if len(parts) != 3 or parts[0] != KEY_BRAND:
        return None
    prefix = parts[1]
    if not prefix:
        return None
    key_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    return prefix, key_hash


async def create_api_key(
    session: AsyncSession,
    *,
    org_id: UUID,
    creator: User,
    name: str,
    requested_scopes: list[str],
    creator_scopes: list[str],
    expires_at: datetime | None = None,
) -> tuple[APIKey, str]:
    """Create a key. Returns ``(api_key, plaintext)``.

    The requested scopes must be a subset of the creator's scopes &mdash; we
    don't allow privilege escalation through key issuance. Wildcards in
    creator scopes are honoured (an OWNER with ``org:*`` can grant any
    ``org:*`` scope).
    """
    from authx._internal._scopes import has_required_scopes

    if not has_required_scopes(requested_scopes, creator_scopes, all_required=True):
        raise ScopeNotPermittedError(requested_scopes)

    plaintext, prefix, key_hash = _generate_key()

    api_key = APIKey(
        org_id=org_id,
        name=name,
        prefix=prefix,
        key_hash=key_hash,
        scopes=requested_scopes,
        expires_at=expires_at,
        created_by_id=creator.id,
    )
    session.add(api_key)
    await session.flush()
    return api_key, plaintext


async def list_api_keys(session: AsyncSession, org_id: UUID) -> list[APIKey]:
    stmt = select(APIKey).where(APIKey.org_id == org_id).order_by(APIKey.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def revoke_api_key(session: AsyncSession, *, org_id: UUID, key_id: UUID) -> None:
    key = await session.get(APIKey, key_id)
    if key is None or key.org_id != org_id:
        raise APIKeyNotFoundError(str(key_id))
    await session.delete(key)
    await session.flush()


async def lookup_by_plaintext(session: AsyncSession, plaintext: str) -> APIKey | None:
    """Find an active API key by plaintext value, or ``None``."""
    parsed = parse_key(plaintext)
    if parsed is None:
        return None
    _prefix, expected_hash = parsed

    stmt = select(APIKey).where(APIKey.key_hash == expected_hash)
    result = await session.execute(stmt)
    key = result.scalar_one_or_none()
    if key is None:
        return None
    if not hmac.compare_digest(key.key_hash, expected_hash):  # pragma: no cover
        return None
    if key.expires_at is not None and key.expires_at < datetime.now(UTC):
        return None
    return key


async def touch_last_used(session: AsyncSession, key: APIKey) -> None:
    key.last_used_at = datetime.now(UTC)
    await session.flush()
