from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.auth.passwords import verify_password
from dogeapi.cli import _create_or_update_admin
from dogeapi.models import User


async def test_create_admin_creates_verified_superadmin(db_session: AsyncSession) -> None:
    status = await _create_or_update_admin(
        session=db_session,
        email="admin@example.com",
        password="correct-horse-battery",
        full_name="Admin User",
        update_password=False,
    )

    result = await db_session.execute(select(User).where(User.email == "admin@example.com"))
    user = result.scalar_one()

    assert status == "created"
    assert user.is_superadmin is True
    assert user.is_active is True
    assert user.email_verified_at is not None
    assert user.full_name == "Admin User"
    assert user.password_hash is not None
    assert verify_password("correct-horse-battery", user.password_hash)


async def test_create_admin_promotes_existing_user_without_password_update(db_session: AsyncSession) -> None:
    user = User(
        email="existing@example.com",
        password_hash=None,
        is_active=False,
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()

    status = await _create_or_update_admin(
        session=db_session,
        email="existing@example.com",
        password="first-password",
        full_name=None,
        update_password=False,
    )

    assert status == "updated"
    assert user.is_superadmin is True
    assert user.is_active is True
    assert user.email_verified_at is not None
    assert user.password_hash is not None
    assert verify_password("first-password", user.password_hash)


async def test_create_admin_keeps_existing_password_unless_requested(db_session: AsyncSession) -> None:
    await _create_or_update_admin(
        session=db_session,
        email="rotate@example.com",
        password="first-password",
        full_name=None,
        update_password=False,
    )

    status = await _create_or_update_admin(
        session=db_session,
        email="rotate@example.com",
        password="second-password",
        full_name=None,
        update_password=False,
    )
    result = await db_session.execute(select(User).where(User.email == "rotate@example.com"))
    user = result.scalar_one()

    assert status == "unchanged"
    assert user.password_hash is not None
    assert verify_password("first-password", user.password_hash)

    status = await _create_or_update_admin(
        session=db_session,
        email="rotate@example.com",
        password="second-password",
        full_name=None,
        update_password=True,
    )

    assert status == "updated"
    assert verify_password("second-password", user.password_hash)
