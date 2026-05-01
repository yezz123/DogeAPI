"""Admin schemas (cross-tenant views)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class AdminTenantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    plan: str
    member_count: int
    created_at: datetime


class AdminUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_superadmin: bool
    email_verified_at: datetime | None
    created_at: datetime


class SystemHealth(BaseModel):
    db_ok: bool
    redis_ok: bool
    total_users: int
    total_orgs: int
    total_api_keys: int
