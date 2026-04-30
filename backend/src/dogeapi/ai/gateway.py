"""Async client for `LLM Gateway <https://api.llmgateway.io>`_.

The gateway exposes an OpenAI-compatible ``/v1/chat/completions`` endpoint
plus a ``/v1/models`` discovery endpoint that returns rich metadata
(pricing, context length, capabilities) we use to drive the UI's model
picker.

The client is purely thin &mdash; we don't depend on the OpenAI SDK because
``httpx`` is already a project dependency and the gateway's surface is
small enough to wrap directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from dogeapi.settings import Settings


DEFAULT_BASE_URL = "https://api.llmgateway.io/v1"
DEFAULT_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


class LLMGatewayError(Exception):
    """Raised when the gateway returns a non-2xx response."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail


@dataclass
class GatewayChatResult:
    """Normalised view of a chat-completion response."""

    text: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: Decimal
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GatewayModel:
    """Subset of the ``/v1/models`` response we care about for the UI."""

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
    raw: dict[str, Any] = field(default_factory=dict)


def _is_configured(settings: Settings) -> bool:
    """``True`` when an API key is present (enabling real gateway calls)."""
    return bool(settings.LLM_GATEWAY_API_KEY)


def _base_url(settings: Settings) -> str:
    """Pick the configured gateway URL, falling back to the public endpoint."""
    return settings.LLM_GATEWAY_URL or DEFAULT_BASE_URL


def _client(settings: Settings) -> httpx.AsyncClient:
    """Build an authenticated ``httpx.AsyncClient`` keyed to the gateway."""
    return httpx.AsyncClient(
        base_url=_base_url(settings),
        timeout=DEFAULT_TIMEOUT,
        headers={
            "Authorization": f"Bearer {settings.LLM_GATEWAY_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )


async def chat_completion(
    settings: Settings,
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float | None = None,
    max_tokens: int | None = None,
    extra: dict[str, Any] | None = None,
) -> GatewayChatResult:
    """POST ``/v1/chat/completions`` and normalise the response.

    Raises :class:`LLMGatewayError` on non-2xx responses.
    """
    payload: dict[str, Any] = {"model": model, "messages": messages}
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if extra:
        payload.update(extra)

    async with _client(settings) as client:
        response = await client.post("/chat/completions", json=payload)

    if response.status_code >= 400:
        raise LLMGatewayError(response.status_code, response.text[:1000])

    body: dict[str, Any] = response.json()
    choices = body.get("choices") or [{}]
    message = choices[0].get("message", {})
    usage = body.get("usage", {}) or {}
    used_model = body.get("model") or model

    cost_raw = usage.get("cost") or 0
    try:
        cost = Decimal(str(cost_raw))
    except Exception:
        cost = Decimal("0")

    return GatewayChatResult(
        text=str(message.get("content") or ""),
        model=used_model,
        tokens_in=int(usage.get("prompt_tokens") or 0),
        tokens_out=int(usage.get("completion_tokens") or 0),
        cost_usd=cost,
        raw=body,
    )


async def list_models(settings: Settings) -> list[GatewayModel]:
    """GET ``/v1/models`` and project the fields useful for our UI."""
    async with _client(settings) as client:
        response = await client.get("/models")

    if response.status_code >= 400:
        raise LLMGatewayError(response.status_code, response.text[:1000])

    items = response.json().get("data") or []
    return [_to_model(entry) for entry in items]


def _to_model(entry: dict[str, Any]) -> GatewayModel:
    arch = entry.get("architecture") or {}
    return GatewayModel(
        id=str(entry.get("id") or ""),
        name=str(entry.get("name") or entry.get("id") or ""),
        family=str(entry.get("family") or "unknown"),
        description=str(entry.get("description") or ""),
        context_length=int(entry.get("context_length") or 0),
        input_modalities=list(arch.get("input_modalities") or []),
        output_modalities=list(arch.get("output_modalities") or []),
        json_output=bool(entry.get("json_output")),
        structured_outputs=bool(entry.get("structured_outputs")),
        free=bool(entry.get("free")),
        deprecated=bool(entry.get("deprecated_at")),
        raw=entry,
    )


__all__ = (
    "DEFAULT_BASE_URL",
    "GatewayChatResult",
    "GatewayModel",
    "LLMGatewayError",
    "_is_configured",
    "chat_completion",
    "list_models",
)
