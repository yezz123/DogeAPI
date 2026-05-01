"""Pydantic request / response models for the auth router."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: PasswordStr
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    email_verified_at: datetime | None
    is_superadmin: bool
    is_active: bool
    created_at: datetime


class RegisterResponse(BaseModel):
    """Response from ``POST /auth/register``.

    Includes a token pair so the client can immediately log in. When email
    delivery is disabled, ``email_verification_link`` is returned so the
    caller can complete verification without an SMTP server.
    """

    user: UserResponse
    tokens: TokenPairResponse
    email_verification_link: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str


class MessageResponse(BaseModel):
    detail: str
