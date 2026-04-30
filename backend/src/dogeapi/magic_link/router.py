"""Magic-link router: ``/auth/magic-link/request`` + ``/consume``."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, EmailStr

from dogeapi.auth.schemas import TokenPairResponse, UserResponse
from dogeapi.auth.service import get_user_by_email
from dogeapi.deps import AuthDep, RedisDep, SessionDep, SettingsDep
from dogeapi.magic_link import service
from dogeapi.models import User

router = APIRouter(prefix="/auth/magic-link", tags=["magic-link"])


class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkRequestResponse(BaseModel):
    detail: str = "Sent"
    link: str | None = None
    """When email delivery is disabled, the link is returned here."""


class MagicLinkConsumeRequest(BaseModel):
    token: str


class MagicLinkConsumeResponse(BaseModel):
    user: UserResponse
    tokens: TokenPairResponse


@router.post("/request", response_model=MagicLinkRequestResponse)
async def request_link(
    body: MagicLinkRequest,
    redis: RedisDep,
    settings: SettingsDep,
    session: SessionDep,
) -> MagicLinkRequestResponse:
    """Issue a magic link for the given email.

    For privacy we always return success so the endpoint can't be used as
    an email enumerator: real users get an email, others see the same
    response but no link is sent.
    """
    ttl = timedelta(minutes=settings.MAGIC_LINK_TTL_MINUTES)
    token = await service.issue(redis, body.email, ttl=ttl)
    link = f"{settings.FRONTEND_BASE_URL}/magic-link?token={token}"

    user = await get_user_by_email(session, body.email)
    if user is None:
        # Don't actually send anything for unknown emails.
        return MagicLinkRequestResponse(detail="Sent")

    if settings.FEATURE_EMAIL_DELIVERY:
        from dogeapi.email import send_magic_link

        await send_magic_link(settings, to=body.email, link=link)
        return MagicLinkRequestResponse(detail="Sent")

    return MagicLinkRequestResponse(detail="Sent (email delivery disabled)", link=link)


@router.post("/consume", response_model=MagicLinkConsumeResponse)
async def consume_link(
    body: MagicLinkConsumeRequest,
    response: Response,
    redis: RedisDep,
    session: SessionDep,
    auth: AuthDep,
    settings: SettingsDep,
) -> MagicLinkConsumeResponse:
    email = await service.consume(redis, body.token)
    if email is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Invalid or expired magic link",
        )

    user = await get_user_by_email(session, email)
    if user is None:
        # Auto-create on first sign-in via magic link
        user = User(email=email, password_hash=None)
        session.add(user)
        await session.flush()

    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
        await session.flush()

    pair = auth.create_token_pair(uid=str(user.id), fresh=True)
    auth.set_access_cookies(pair.access_token, response)
    auth.set_refresh_cookies(pair.refresh_token, response)

    return MagicLinkConsumeResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenPairResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
        ),
    )
