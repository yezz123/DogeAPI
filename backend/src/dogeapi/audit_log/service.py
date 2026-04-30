"""Helpers for writing audit log rows.

Service modules can call :func:`record` directly with rich metadata; the
middleware uses the same primitive for automatic capture.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.models import AuditLog


async def record(
    session: AsyncSession,
    *,
    org_id: UUID | None,
    actor_id: UUID | None,
    action: str,
    method: str,
    path: str,
    status_code: int,
    target_type: str | None = None,
    target_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    extra: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        org_id=org_id,
        actor_id=actor_id,
        action=action,
        method=method,
        path=path,
        status_code=status_code,
        target_type=target_type,
        target_id=target_id,
        ip=ip,
        user_agent=user_agent,
        extra=extra or {},
    )
    session.add(entry)
    await session.flush()
    return entry


async def list_logs(
    session: AsyncSession,
    *,
    org_id: UUID | None = None,
    action: str | None = None,
    actor_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    stmt = select(AuditLog)
    if org_id is not None:
        stmt = stmt.where(AuditLog.org_id == org_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_id is not None:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())
