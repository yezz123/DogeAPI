"""Organization (tenant) model.

Slugs are URL-friendly and unique across the entire deployment. The
``plan`` column is a free-form string for now; P9 introduces a richer
billing-aware view.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dogeapi.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(32), nullable=False, default="free", server_default="free")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug!r}>"
