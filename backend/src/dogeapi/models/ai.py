"""AI chat models: threads + messages."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from dogeapi.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_threads"
    __table_args__ = (Index("ix_ai_threads_org_user", "org_id", "user_id"),)

    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New conversation")


class AIMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_messages"
    __table_args__ = (Index("ix_ai_messages_thread_created", "thread_id", "created_at"),)

    thread_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ai_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
