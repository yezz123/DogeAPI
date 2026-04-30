"""Audit log model.

One row per mutating request. The middleware in :mod:`dogeapi.audit_log`
fills these in after every 2xx mutation; service modules can also call
``audit_log.record(...)`` directly for richer metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from dogeapi.models.base import Base, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Audit log row.

    ``org_id`` and ``actor_id`` are *soft* references (no DB-level FK):
    the audit history must survive deletion of the underlying entity, and
    we never want a deletion cascade or SET NULL to mutate audit rows.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_created", "org_id", "created_at"),
        Index("ix_audit_logs_org_action", "org_id", "action"),
    )

    org_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    method: Mapped[str] = mapped_column(String(8), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    status_code: Mapped[int] = mapped_column(nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB(), nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
