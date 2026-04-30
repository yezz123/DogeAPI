"""Admin router: cross-tenant views for SaaS operators."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from dogeapi.admin.dependencies import require_superadmin
from dogeapi.admin.schemas import (
    AdminTenantSummary,
    AdminUserSummary,
    SystemHealth,
)
from dogeapi.audit_log import service as audit_service
from dogeapi.audit_log.schemas import AuditLogEntry
from dogeapi.deps import RedisDep, SessionDep
from dogeapi.models import APIKey, Membership, Organization, User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_superadmin)],
)


@router.get("/tenants", response_model=list[AdminTenantSummary])
async def list_tenants(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AdminTenantSummary]:
    """List every organization and its member count."""
    stmt = (
        select(
            Organization.id,
            Organization.slug,
            Organization.name,
            Organization.plan,
            Organization.created_at,
            func.count(Membership.id).label("member_count"),
        )
        .outerjoin(Membership, Membership.org_id == Organization.id)
        .group_by(Organization.id)
        .order_by(Organization.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).all()
    return [
        AdminTenantSummary(
            id=r.id,
            slug=r.slug,
            name=r.name,
            plan=r.plan,
            member_count=r.member_count,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/tenants/{tenant_id}", response_model=AdminTenantSummary)
async def get_tenant(
    tenant_id: UUID,
    session: SessionDep,
) -> AdminTenantSummary:
    org = await session.get(Organization, tenant_id)
    if org is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant not found")
    member_count = await session.scalar(select(func.count(Membership.id)).where(Membership.org_id == org.id)) or 0
    return AdminTenantSummary(
        id=org.id,
        slug=org.slug,
        name=org.name,
        plan=org.plan,
        member_count=member_count,
        created_at=org.created_at,
    )


@router.get("/users", response_model=list[AdminUserSummary])
async def list_users(
    session: SessionDep,
    email: Annotated[str | None, Query(description="Filter by email substring")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AdminUserSummary]:
    stmt = select(User).order_by(User.created_at.desc())
    if email:
        stmt = stmt.where(User.email.ilike(f"%{email}%"))
    stmt = stmt.limit(limit).offset(offset)
    rows = (await session.execute(stmt)).scalars().all()
    return [AdminUserSummary.model_validate(u) for u in rows]


@router.get("/audit-log", response_model=list[AuditLogEntry])
async def cross_tenant_audit_log(
    session: SessionDep,
    org_id: Annotated[UUID | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    actor_id: Annotated[UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogEntry]:
    rows = await audit_service.list_logs(
        session,
        org_id=org_id,
        action=action,
        actor_id=actor_id,
        limit=limit,
        offset=offset,
    )
    return [AuditLogEntry.model_validate(r) for r in rows]


@router.get("/system-health", response_model=SystemHealth)
async def system_health(
    session: SessionDep,
    redis: RedisDep,
) -> SystemHealth:
    db_ok = True
    try:
        await session.scalar(select(1))
    except SQLAlchemyError:
        db_ok = False

    redis_ok = True
    try:
        pong = await redis.ping()
        redis_ok = bool(pong)
    except Exception:
        redis_ok = False

    total_users = await session.scalar(select(func.count(User.id))) or 0
    total_orgs = await session.scalar(select(func.count(Organization.id))) or 0
    total_api_keys = await session.scalar(select(func.count(APIKey.id))) or 0

    return SystemHealth(
        db_ok=db_ok,
        redis_ok=redis_ok,
        total_users=total_users,
        total_orgs=total_orgs,
        total_api_keys=total_api_keys,
    )
