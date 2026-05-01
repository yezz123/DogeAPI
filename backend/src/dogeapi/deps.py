"""Common FastAPI dependencies.

Centralised so feature modules don't reach into each other.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from authx import AuthX, TokenPayload
from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.auth.service import get_user_by_id
from dogeapi.db import get_session
from dogeapi.models import Role, User
from dogeapi.settings import Settings, get_settings


@lru_cache(maxsize=1)
def _get_redis() -> Redis:
    """Process-wide async Redis client."""
    return Redis.from_url(get_settings().REDIS_URL, decode_responses=False)


async def get_redis() -> AsyncIterator[Redis]:
    """FastAPI dep for the Redis client."""
    yield _get_redis()


def get_authx_from_request(request: Request) -> AuthX:
    """Pull the per-app AuthX instance off ``app.state``."""
    auth: AuthX = request.app.state.authx
    return auth


async def get_token_payload(
    request: Request,
    auth: Annotated[AuthX, Depends(get_authx_from_request)],
) -> TokenPayload:
    """Require a valid access token and return its payload."""
    payload: TokenPayload = await auth.access_token_required(request=request)
    return payload


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> User:
    """Resolve the authenticated user from the token's ``sub`` claim.

    Also stashes the user id on ``request.state.audit_actor_id`` for the
    audit log middleware.
    """
    try:
        user_id = UUID(str(payload.sub))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token subject") from exc

    user = await get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    request.state.audit_actor_id = str(user.id)
    return user


def _token_extra(payload: TokenPayload, key: str) -> object | None:
    """Pull a custom claim from the token, regardless of where pydantic stored it.

    ``model_extra`` is the canonical Pydantic 2 location for ``extra="allow"``
    fields; we fall back to ``getattr`` for forward-compat.
    """
    extras = payload.model_extra or {}
    if key in extras:
        return extras[key]
    return getattr(payload, key, None)


async def get_active_org_id(
    request: Request,
    payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UUID:
    """Extract ``org_id`` claim from the access token.

    Also stashes ``request.state.audit_org_id`` for the audit middleware.
    """
    org_id = _token_extra(payload, "org_id")
    if not org_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No active organization in token")
    try:
        org_uuid = UUID(str(org_id))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid org_id claim") from exc
    request.state.audit_org_id = str(org_uuid)
    return org_uuid


async def get_active_role(
    payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> Role:
    """Extract the caller's role for the active org from the JWT data claim."""
    raw_role = _token_extra(payload, "role")
    if not raw_role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No role in token")
    try:
        return Role(str(raw_role))
    except ValueError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid role claim") from exc


def get_app_settings(request: Request) -> Settings:
    """Return the per-app ``Settings`` (set in :func:`dogeapi.main.create_app`).

    Falling back to :func:`get_settings` keeps the dep usable from contexts
    that don't have a request-bound app (e.g. ad-hoc scripts).
    """
    state_settings = getattr(request.app.state, "settings", None)
    if isinstance(state_settings, Settings):
        return state_settings
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
AuthDep = Annotated[AuthX, Depends(get_authx_from_request)]
TokenDep = Annotated[TokenPayload, Depends(get_token_payload)]
UserDep = Annotated[User, Depends(get_current_user)]
OrgIdDep = Annotated[UUID, Depends(get_active_org_id)]
RoleDep = Annotated[Role, Depends(get_active_role)]
