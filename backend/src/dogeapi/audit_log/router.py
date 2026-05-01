"""Audit log router."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from dogeapi.audit_log import service
from dogeapi.audit_log.schemas import AuditLogEntry
from dogeapi.deps import SessionDep
from dogeapi.security import OrgMatch, require_scope

router = APIRouter(tags=["audit-log"])


@router.get(
    "/orgs/{slug}/audit-log",
    response_model=list[AuditLogEntry],
    dependencies=[Depends(require_scope("org:audit:read"))],
)
async def list_org_audit_log(
    org: OrgMatch,
    session: SessionDep,
    action: Annotated[str | None, Query(description="Filter by action")] = None,
    actor_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogEntry]:
    rows = await service.list_logs(
        session,
        org_id=org.id,
        action=action,
        actor_id=actor_id,
        limit=limit,
        offset=offset,
    )
    return [AuditLogEntry.model_validate(row) for row in rows]
