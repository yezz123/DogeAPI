"""FastAPI deps for ``X-API-Key`` authentication.

When a request carries ``X-API-Key``, we resolve the key to a synthetic
``TokenPayload`` carrying the key's scopes and ``org_id``. Routes that are
already protected by JWT scope-required deps can opt-in to API-key auth via
``require_jwt_or_api_key_scope`` instead of ``require_scope``.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from authx import TokenPayload
from authx._internal._scopes import has_required_scopes
from authx.exceptions import InsufficientScopeError, MissingTokenError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.api_keys.service import lookup_by_plaintext, touch_last_used
from dogeapi.db import get_session
from dogeapi.deps import SettingsDep
from dogeapi.models import APIKey

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def _synthetic_payload(api_key: APIKey) -> TokenPayload:
    """Build a TokenPayload representing the API key's identity + scopes."""
    return TokenPayload(
        sub=f"apikey:{api_key.id}",
        type="access",
        scopes=list(api_key.scopes),
        # custom claims via extra="allow"
        org_id=str(api_key.org_id),  # type: ignore[call-arg]
        api_key_id=str(api_key.id),  # type: ignore[call-arg]
    )


async def api_key_payload(
    settings: SettingsDep,
    session: Annotated[AsyncSession, Depends(get_session)],
    api_key_header: Annotated[str | None, Depends(API_KEY_HEADER)],
) -> TokenPayload | None:
    """Resolve ``X-API-Key`` into a synthetic ``TokenPayload``, or None."""
    if api_key_header is None:
        return None
    if not settings.FEATURE_API_KEYS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "API keys are disabled")

    key = await lookup_by_plaintext(session, api_key_header)
    if key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")

    await touch_last_used(session, key)
    return _synthetic_payload(key)


async def api_key_or_jwt_payload(
    request: Request,
    api_key: Annotated[TokenPayload | None, Depends(api_key_payload)],
) -> TokenPayload:
    """Prefer an X-API-Key payload, else fall back to JWT.

    Raises 401 if neither is present.
    """
    if api_key is not None:
        return api_key
    auth = request.app.state.authx
    try:
        payload: TokenPayload = await auth.access_token_required(request=request)
    except MissingTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required") from exc
    return payload


def require_api_key_scope(*scopes: str, all_required: bool = True) -> Callable[..., Coroutine[Any, Any, TokenPayload]]:
    """Dep enforcing scopes against an X-API-Key only (no JWT fallback)."""

    async def _check(
        payload: Annotated[TokenPayload | None, Depends(api_key_payload)],
    ) -> TokenPayload:
        if payload is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key required")
        if not has_required_scopes(list(scopes), payload.scopes, all_required=all_required):
            raise InsufficientScopeError(required=list(scopes), provided=payload.scopes)
        return payload

    return _check


def require_jwt_or_api_key_scope(
    *scopes: str, all_required: bool = True
) -> Callable[..., Coroutine[Any, Any, TokenPayload]]:
    """Dep that enforces scopes against either an API key or JWT."""

    async def _check(
        payload: Annotated[TokenPayload, Depends(api_key_or_jwt_payload)],
    ) -> TokenPayload:
        if not has_required_scopes(list(scopes), payload.scopes, all_required=all_required):
            raise InsufficientScopeError(required=list(scopes), provided=payload.scopes)
        return payload

    return _check
