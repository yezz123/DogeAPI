"""Stripe subscription model.

One row per organization. Soft references for ``org_id`` so we can keep
billing history if an org is deleted, though in practice the cascade is
fine for a v1.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from dogeapi.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Subscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    plan: Mapped[str] = mapped_column(String(32), nullable=False, default="free", server_default="free")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
