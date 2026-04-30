"""Membership: a user's role inside an organization."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from dogeapi.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Role(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

    @property
    def rank(self) -> int:
        """Higher rank = more authority. Used for "can demote/promote?" checks."""
        return {Role.OWNER: 3, Role.ADMIN: 2, Role.MEMBER: 1}[self]


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "org_id", name="uq_memberships_user_org"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Membership user={self.user_id} org={self.org_id} role={self.role.value}>"
