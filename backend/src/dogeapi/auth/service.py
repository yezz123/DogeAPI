"""Auth business logic separated from the router.

Keeping these functions stateless and explicit means we can unit-test
each branch without spinning up FastAPI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.auth.passwords import hash_password, needs_rehash, verify_password
from dogeapi.models import User


class EmailAlreadyRegisteredError(Exception):
    """Raised when registration hits the unique-email constraint."""


class InvalidCredentialsError(Exception):
    """Raised on bad email or password during login."""


class UserNotFoundError(Exception):
    """Raised when a lookup fails."""


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def register_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    """Create a new user. Raises :class:`EmailAlreadyRegisteredError`."""
    existing = await get_user_by_email(session, email)
    if existing is not None:
        raise EmailAlreadyRegisteredError(email)

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    session.add(user)
    await session.flush()
    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User:
    """Verify credentials and return the user. Raises on failure."""
    user = await get_user_by_email(session, email)
    if user is None or user.password_hash is None:
        raise InvalidCredentialsError
    if not user.is_active:
        raise InvalidCredentialsError
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        await session.flush()
    return user


async def mark_email_verified(session: AsyncSession, user_id: UUID) -> User:
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UserNotFoundError(str(user_id))
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
        await session.flush()
    return user
