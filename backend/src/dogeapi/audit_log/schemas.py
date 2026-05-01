"""Audit log API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID | None
    actor_id: UUID | None
    action: str
    target_type: str | None
    target_id: str | None
    method: str
    path: str
    status_code: int
    ip: str | None
    user_agent: str | None
    extra: dict[str, Any]
    created_at: datetime
