"""Operational CLI for local and container bootstrap tasks."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from typing import Annotated

import typer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.auth.passwords import hash_password
from dogeapi.db import get_engine
from dogeapi.models import User

app = typer.Typer(help="AI Template operational commands.")
admin_app = typer.Typer(help="Manage super-admin accounts.")
app.add_typer(admin_app, name="admin")


def _env_default(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


async def _create_or_update_admin(
    *,
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str | None,
    update_password: bool,
) -> str:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_active=True,
            is_superadmin=True,
            email_verified_at=datetime.now(UTC),
        )
        session.add(user)
        await session.flush()
        return "created"

    changed = False
    if not user.is_superadmin:
        user.is_superadmin = True
        changed = True
    if not user.is_active:
        user.is_active = True
        changed = True
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
        changed = True
    if full_name and user.full_name != full_name:
        user.full_name = full_name
        changed = True
    if update_password or user.password_hash is None:
        user.password_hash = hash_password(password)
        changed = True

    if changed:
        await session.flush()
        return "updated"

    return "unchanged"


async def _create_or_update_admin_from_settings(
    *,
    email: str,
    password: str,
    full_name: str | None,
    update_password: bool,
) -> str:
    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        status = await _create_or_update_admin(
            session=session,
            email=email,
            password=password,
            full_name=full_name,
            update_password=update_password,
        )
        await session.commit()
        return status


@admin_app.command("create")
def create_admin(
    email: Annotated[
        str | None,
        typer.Option(
            "--email",
            "-e",
            envvar="ADMIN_EMAIL",
            help="Super-admin email. Can also be set with ADMIN_EMAIL.",
        ),
    ] = None,
    password: Annotated[
        str | None,
        typer.Option(
            "--password",
            "-p",
            envvar="ADMIN_PASSWORD",
            help="Super-admin password. Can also be set with ADMIN_PASSWORD.",
        ),
    ] = None,
    full_name: Annotated[
        str | None,
        typer.Option(
            "--full-name",
            "-n",
            envvar="ADMIN_FULL_NAME",
            help="Optional display name. Can also be set with ADMIN_FULL_NAME.",
        ),
    ] = None,
    update_password: Annotated[
        bool,
        typer.Option(
            "--update-password/--keep-password",
            help="Update the password if the admin already exists.",
        ),
    ] = False,
) -> None:
    """Create or promote a super-admin account.

    The command is idempotent: existing users are promoted, activated, and
    marked verified. Passwords are preserved unless ``--update-password`` is
    passed or the existing account has no password.
    """
    email = (email or _env_default("ADMIN_EMAIL") or "").strip().lower()
    password = password or _env_default("ADMIN_PASSWORD")
    full_name = full_name or _env_default("ADMIN_FULL_NAME")

    if not email:
        raise typer.BadParameter("Provide --email or ADMIN_EMAIL.")
    if not password:
        raise typer.BadParameter("Provide --password or ADMIN_PASSWORD.")
    if len(password) < 8:
        raise typer.BadParameter("Admin password must be at least 8 characters.")

    status = asyncio.run(
        _create_or_update_admin_from_settings(
            email=email,
            password=password,
            full_name=full_name,
            update_password=update_password,
        )
    )
    typer.echo(f"Super-admin {email} {status}.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
