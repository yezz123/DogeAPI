"""LLM agent layer.

Two implementations:

- :class:`_LLMGatewayAgent` &mdash; talks to the public LLM Gateway service
  (or any OpenAI-compatible URL configured via ``LLM_GATEWAY_URL``).
- :class:`_EchoAgent` &mdash; deterministic offline fallback used in tests
  and local dev when no API key is configured.

The :func:`get_agent` selector picks the right one per ``Settings``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from dogeapi.ai import gateway
from dogeapi.ai.gateway import GatewayChatResult

if TYPE_CHECKING:
    from dogeapi.settings import Settings


@dataclass
class AgentResponse:
    text: str
    tokens_in: int
    tokens_out: int
    model: str
    cost_usd: Decimal = Decimal("0")
    extra: dict[str, Any] = field(default_factory=dict)


SYSTEM_PROMPT = (
    "You are a helpful assistant for a multi-tenant SaaS app. Answer concisely and quote sources when uncertain."
)


class _EchoAgent:
    """Offline agent used when no gateway key is configured.

    Returns a deterministic ``echo: …`` response so tests run without
    network access. The reported model is always ``"echo"`` regardless of
    what the caller asked for &mdash; the echo agent is the *actual* model
    in use.
    """

    name = "echo"

    async def respond(self, messages: list[dict[str, str]], *, model: str | None = None) -> AgentResponse:
        del model  # ignored; we always return "echo"
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "",
        )
        text = f"echo: {last_user}".strip() or "echo: (empty)"
        return AgentResponse(
            text=text,
            tokens_in=sum(len(m["content"].split()) for m in messages),
            tokens_out=len(text.split()),
            model="echo",
            cost_usd=Decimal("0"),
        )


class _LLMGatewayAgent:
    """Live agent backed by the LLM Gateway HTTP API."""

    def __init__(self, settings: Settings, default_model: str) -> None:
        self._settings = settings
        self.name = default_model

    async def respond(self, messages: list[dict[str, str]], *, model: str | None = None) -> AgentResponse:
        full_messages: list[dict[str, str]] = []
        if not any(m["role"] == "system" for m in messages):
            full_messages.append({"role": "system", "content": SYSTEM_PROMPT})
        full_messages.extend(messages)

        result: GatewayChatResult = await gateway.chat_completion(
            self._settings,
            model=model or self.name,
            messages=full_messages,
        )
        return AgentResponse(
            text=result.text,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            model=result.model,
            cost_usd=result.cost_usd,
            extra={
                "request_id": (result.raw.get("metadata") or {}).get("request_id"),
                "used_provider": (result.raw.get("metadata") or {}).get("used_provider"),
            },
        )


def get_agent(settings: Settings) -> _EchoAgent | _LLMGatewayAgent:
    """Build the agent for the given settings.

    No caching: tests want a fresh agent per ``Settings`` instance, and
    instantiation is cheap.
    """
    if gateway._is_configured(settings):
        return _LLMGatewayAgent(settings, settings.AI_DEFAULT_MODEL)
    return _EchoAgent()


# Back-compat shim: a module-level cache used to live here.
def get_agent_factory():  # type: ignore[no-untyped-def]  # pragma: no cover
    """Deprecated: kept so existing tests can call ``cache_clear()`` no-op."""

    class _Factory:
        @staticmethod
        def cache_clear() -> None:
            return None

    return _Factory()


# Keep ``cache_clear`` available on the module-level factory for tests.
get_agent_factory.cache_clear = lambda: None  # type: ignore[attr-defined]
