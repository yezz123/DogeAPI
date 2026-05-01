"""Password reset endpoints + Redis-backed tokens."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, StringConstraints
from redis.asyncio import Redis

from dogeapi.auth.passwords import hash_password
from dogeapi.auth.schemas import MessageResponse
from dogeapi.auth.service import get_user_by_email
from dogeapi.deps import RedisDep, SessionDep, SettingsDep
from dogeapi.models import User

router = APIRouter(prefix="/auth/password-reset", tags=["auth"])

PREFIX = "pwreset:"
TTL = timedelta(hours=1)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def _issue(redis: Redis, user_id: UUID) -> str:
    token = secrets.token_urlsafe(32)
    await redis.setex(f"{PREFIX}{_hash(token)}", int(TTL.total_seconds()), str(user_id))
    return token


async def _consume(redis: Redis, token: str) -> UUID | None:
    key = f"{PREFIX}{_hash(token)}"
    pipe = redis.pipeline()
    pipe.get(key)
    pipe.delete(key)
    raw_user_id, _ = await pipe.execute()
    if not raw_user_id:
        return None
    return UUID(raw_user_id.decode("utf-8") if isinstance(raw_user_id, bytes) else raw_user_id)


PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetRequestResponse(BaseModel):
    detail: str = "If that email exists, a reset link has been sent."
    link: str | None = None


class PasswordResetConsumeRequest(BaseModel):
    token: str
    new_password: PasswordStr


@router.post("/request", response_model=PasswordResetRequestResponse)
async def request_reset(
    body: PasswordResetRequest,
    session: SessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> PasswordResetRequestResponse:
    """Request a password reset link.

    Always returns 200 to avoid leaking which emails are registered.
    """
    user = await get_user_by_email(session, body.email)
    if user is None:
        return PasswordResetRequestResponse()

    token = await _issue(redis, user.id)
    link = f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}"

    if settings.FEATURE_EMAIL_DELIVERY:
        from dogeapi.email import send_password_reset

        await send_password_reset(settings, to=user.email, link=link)
        return PasswordResetRequestResponse()

    return PasswordResetRequestResponse(
        detail="If that email exists, a reset link has been sent (email delivery disabled).",
        link=link,
    )


@router.post("/consume", response_model=MessageResponse)
async def consume_reset(
    body: PasswordResetConsumeRequest,
    session: SessionDep,
    redis: RedisDep,
) -> MessageResponse:
    user_id = await _consume(redis, body.token)
    if user_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Invalid or expired reset token",
        )
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User no longer exists")
    user.password_hash = hash_password(body.new_password)
    await session.flush()
    return MessageResponse(detail="Password updated")
