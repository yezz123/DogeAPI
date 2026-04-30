"""Pydantic schemas for the API keys endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

KeyName = Annotated[str, StringConstraints(min_length=1, max_length=120)]


class APIKeyCreate(BaseModel):
    name: KeyName
    scopes: list[str] = Field(default_factory=list, max_length=64)
    expires_at: datetime | None = None


class APIKeyResponse(BaseModel):
    """A safe view of an API key &mdash; never includes the plaintext key."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    name: str
    prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class APIKeyCreatedResponse(BaseModel):
    """Returned exactly once on creation."""

    api_key: APIKeyResponse
    plaintext_key: str
    """The full key &mdash; show to the user once and never again."""
