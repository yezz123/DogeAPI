"""Middleware that captures audit log rows after every successful mutation.

The middleware runs *after* ``call_next``, so dependencies have already
populated ``request.state`` with ``actor_id`` and ``org_id`` (when
applicable). It only records 2xx responses to mutating methods so failed
requests don't pollute the log.

Errors in the audit write are swallowed and logged: a broken audit pipe
must never break the user-facing request.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from dogeapi.audit_log.service import record

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine
    from starlette.requests import Request
    from starlette.responses import Response

logger = logging.getLogger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_PATH_TO_ACTION = [
    (re.compile(r"^/orgs/[^/]+/invitations/[^/]+/?$"), "invitation"),
    (re.compile(r"^/orgs/[^/]+/invitations/?$"), "invitation"),
    (re.compile(r"^/orgs/[^/]+/members/[^/]+/?$"), "member"),
    (re.compile(r"^/orgs/[^/]+/members/?$"), "member"),
    (re.compile(r"^/orgs/[^/]+/api-keys/[^/]+/?$"), "apikey"),
    (re.compile(r"^/orgs/[^/]+/api-keys/?$"), "apikey"),
    (re.compile(r"^/orgs/[^/]+/switch/?$"), "org_switch"),
    (re.compile(r"^/orgs/[^/]+/leave/?$"), "org_leave"),
    (re.compile(r"^/orgs/[^/]+/?$"), "org"),
    (re.compile(r"^/orgs/?$"), "org"),
    (re.compile(r"^/invitations/accept/?$"), "invitation_accept"),
    (re.compile(r"^/auth/register/?$"), "auth_register"),
    (re.compile(r"^/auth/login/?$"), "auth_login"),
    (re.compile(r"^/auth/logout/?$"), "auth_logout"),
    (re.compile(r"^/auth/verify-email/?$"), "auth_verify_email"),
]

_VERBS = {"POST": "created", "PUT": "updated", "PATCH": "updated", "DELETE": "deleted"}


def _classify(path: str, method: str) -> tuple[str, str | None]:
    """Return ``(action, target_type)`` from a URL path + method."""
    for regex, target in _PATH_TO_ACTION:
        if regex.match(path):
            verb = _VERBS.get(method, method.lower())
            return f"{target}.{verb}", target
    return f"http.{method.lower()}", None


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Records an audit log row after every successful mutation."""

    def __init__(self, app: ASGIApp, *, engine: AsyncEngine) -> None:
        super().__init__(app)
        self._sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)

        try:
            if request.method in MUTATING_METHODS and 200 <= response.status_code < 400:
                await self._write(request, response)
        except Exception:  # pragma: no cover
            logger.exception("audit log write failed")

        return response

    async def _write(self, request: Request, response: Response) -> None:
        actor_id_raw = getattr(request.state, "audit_actor_id", None)
        org_id_raw = getattr(request.state, "audit_org_id", None)
        actor_id = UUID(str(actor_id_raw)) if actor_id_raw else None
        org_id = UUID(str(org_id_raw)) if org_id_raw else None

        action, target_type = _classify(request.url.path, request.method)

        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")

        async with self._sessionmaker() as session:
            await record(
                session,
                org_id=org_id,
                actor_id=actor_id,
                action=action,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                target_type=target_type,
                ip=ip,
                user_agent=ua,
            )
            await session.commit()
