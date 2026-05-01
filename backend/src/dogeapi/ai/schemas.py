"""AI chat API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ContentStr = Annotated[str, StringConstraints(min_length=1, max_length=20_000)]
TitleStr = Annotated[str, StringConstraints(min_length=1, max_length=255)]
ModelStr = Annotated[str, StringConstraints(min_length=1, max_length=120)]


class ThreadCreate(BaseModel):
    title: TitleStr | None = None
    default_model: ModelStr | None = None


class MessageRequest(BaseModel):
    content: ContentStr
    model: ModelStr | None = None


class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    org_id: UUID
    user_id: UUID
    title: str
    default_model: str | None
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
    cost_usd: Decimal
    extra: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    monthly_tokens_used: int
    monthly_token_limit: int | None


class ThreadDetailResponse(BaseModel):
    thread: ThreadResponse
    messages: list[MessageResponse] = Field(default_factory=list)


# ─── Models discovery ────────────────────────────────────────────────────


class ModelInfo(BaseModel):
    id: str
    name: str
    family: str
    description: str
    context_length: int
    input_modalities: list[str]
    output_modalities: list[str]
    json_output: bool
    structured_outputs: bool
    free: bool
    deprecated: bool


class ModelsListResponse(BaseModel):
    configured: bool
    """``False`` when no LLM Gateway API key is configured (echo agent in use)."""
    default_model: str
    models: list[ModelInfo]
