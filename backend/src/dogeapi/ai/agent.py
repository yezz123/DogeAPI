"""Pydantic AI agent factory.

We build a single agent per process and reuse it across requests. The
provider is selected via env vars; if none is configured we fall back to
a deterministic "echo" agent suitable for local development.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dogeapi.settings import Settings


@dataclass
class AgentResponse:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


class _EchoAgent:
    """Deterministic offline agent for development without an API key."""

    name = "echo"

    async def respond(self, messages: list[dict[str, str]]) -> AgentResponse:
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "",
        )
        text = f"echo: {last_user}".strip()
        return AgentResponse(
            text=text or "echo: (empty)",
            tokens_in=sum(len(m["content"].split()) for m in messages),
            tokens_out=len(text.split()),
            model="echo",
        )


class _PydanticAIAgent:
    """Real LLM agent using Pydantic AI."""

    def __init__(self, model_name: str) -> None:
        from pydantic_ai import Agent

        self.name = model_name
        self._agent: Agent[None, str] = Agent(
            model_name,
            system_prompt=(
                "You are a helpful assistant for a multi-tenant SaaS app. "
                "Answer concisely and quote sources when uncertain."
            ),
        )

    async def respond(self, messages: list[dict[str, str]]) -> AgentResponse:
        history = [m for m in messages if m["role"] in {"user", "assistant"}]
        user_input = "" if not history else history[-1]["content"]

        result = await self._agent.run(user_input)
        text = str(result.data)
        usage = result.usage()
        return AgentResponse(
            text=text,
            tokens_in=int(usage.request_tokens or 0),
            tokens_out=int(usage.response_tokens or 0),
            model=self.name,
        )


@lru_cache(maxsize=1)
def get_agent_factory():  # type: ignore[no-untyped-def]
    """Returned function yields the appropriate agent for the configured env."""

    def _factory(settings: Settings):  # type: ignore[no-untyped-def]
        # If LLM_GATEWAY_URL is set, route OpenAI calls through it
        if settings.LLM_GATEWAY_URL and settings.LLM_GATEWAY_API_KEY:
            os.environ.setdefault("OPENAI_BASE_URL", settings.LLM_GATEWAY_URL)
            os.environ.setdefault("OPENAI_API_KEY", settings.LLM_GATEWAY_API_KEY)

        if settings.OPENAI_API_KEY:
            os.environ.setdefault("OPENAI_API_KEY", settings.OPENAI_API_KEY)
            try:
                return _PydanticAIAgent(f"openai:{settings.AI_DEFAULT_MODEL}")
            except Exception:
                pass

        if settings.ANTHROPIC_API_KEY:
            os.environ.setdefault("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)
            try:
                return _PydanticAIAgent(f"anthropic:{settings.AI_DEFAULT_MODEL}")
            except Exception:
                pass

        return _EchoAgent()

    return _factory


def get_agent(settings: Settings):  # type: ignore[no-untyped-def]
    return get_agent_factory()(settings)
