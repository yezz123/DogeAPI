"""AI chat API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ContentStr = Annotated[str, StringConstraints(min_length=1, max_length=20_000)]
TitleStr = Annotated[str, StringConstraints(min_length=1, max_length=255)]


class ThreadCreate(BaseModel):
    title: TitleStr | None = None


class MessageRequest(BaseModel):
    content: ContentStr


class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    role: str
    content: str
    tokens_in: int
    tokens_out: int
    model: str | None
    created_at: datetime


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    monthly_tokens_used: int
    monthly_token_limit: int | None


class ThreadDetailResponse(BaseModel):
    thread: ThreadResponse
    messages: list[MessageResponse] = Field(default_factory=list)
