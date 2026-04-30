"""Domain logic for OAuth sign-in: find-or-create user + link account."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.auth.service import get_user_by_email
from dogeapi.models import OAuthAccount, User


async def upsert_user_from_oauth(
    session: AsyncSession,
    *,
    provider: str,
    provider_account_id: str,
    email: str,
    full_name: str | None = None,
) -> User:
    """Find or create a user matching the OAuth identity.

    Resolution order:

    1. Existing :class:`OAuthAccount` for ``(provider, provider_account_id)``
       - return its user.
    2. Existing :class:`User` matching ``email`` - link the account.
    3. Create a new user (no password) and link the account.
    """
    stmt = select(OAuthAccount).where(
        OAuthAccount.provider == provider,
        OAuthAccount.provider_account_id == provider_account_id,
    )
    existing_link = (await session.execute(stmt)).scalar_one_or_none()
    if existing_link is not None:
        user = await session.get(User, existing_link.user_id)
        assert user is not None
        return user

    user = await get_user_by_email(session, email)
    if user is None:
        user = User(email=email, full_name=full_name, password_hash=None)
        session.add(user)
        await session.flush()

    link = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_account_id=provider_account_id,
        email=email,
    )
    session.add(link)
    await session.flush()
    return user
