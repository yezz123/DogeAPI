"""Pydantic schemas for organization endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from dogeapi.models import Role

SlugStr = Annotated[
    str,
    StringConstraints(
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
    ),
]


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: SlugStr | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    plan: str
    created_at: datetime


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    org_id: UUID
    role: Role
    created_at: datetime


class OrgWithRoleResponse(BaseModel):
    """Organization plus the caller's role in it."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    plan: str
    created_at: datetime
    role: Role


class MemberSummary(BaseModel):
    """Member listing item joining users + memberships."""

    user_id: UUID
    email: EmailStr
    full_name: str | None
    role: Role
    created_at: datetime


class InviteCreate(BaseModel):
    email: EmailStr
    role: Role = Role.MEMBER


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    email: EmailStr
    role: Role
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime


class InvitationCreatedResponse(BaseModel):
    invitation: InvitationResponse
    invite_link: str | None = None
    """Returned when ``FEATURE_EMAIL_DELIVERY`` is off."""


class AcceptInviteRequest(BaseModel):
    token: str


class RoleChangeRequest(BaseModel):
    role: Role


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
