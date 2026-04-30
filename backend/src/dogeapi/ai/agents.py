"""Pydantic AI integration on top of the LLM Gateway.

Pydantic AI's :class:`Agent` is the right primitive for higher-level LLM
work &mdash; structured outputs, tool calls, multi-step workflows. Because
the gateway is OpenAI-compatible we can plug it in as a regular
``OpenAIProvider`` and get every model the gateway exposes for free.

This module provides:

- :func:`build_agent` &mdash; the canonical factory that returns a typed
  :class:`Agent` configured against the gateway.
- :func:`gateway_model` &mdash; lower-level helper that constructs only the
  underlying ``OpenAIChatModel`` if you need full agent control.

The optional ``ai`` extra must be installed (``uv sync --extra ai``).
The :func:`build_agent` function raises :class:`RuntimeError` when called
without ``LLM_GATEWAY_API_KEY`` configured so callers fail fast.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeVar

from dogeapi.ai.gateway import DEFAULT_BASE_URL

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel

    from dogeapi.settings import Settings


OutputT = TypeVar("OutputT")
DepsT = TypeVar("DepsT")


class GatewayNotConfiguredError(RuntimeError):
    """Raised when an agent is built without a gateway API key."""


def gateway_model(
    settings: Settings,
    *,
    model: str | None = None,
) -> OpenAIChatModel:
    """Return a Pydantic AI ``OpenAIChatModel`` pointed at the gateway."""
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    if not settings.LLM_GATEWAY_API_KEY:
        raise GatewayNotConfiguredError("LLM_GATEWAY_API_KEY is empty; set it in your .env to use Pydantic AI.")

    provider = OpenAIProvider(
        base_url=settings.LLM_GATEWAY_URL or DEFAULT_BASE_URL,
        api_key=settings.LLM_GATEWAY_API_KEY,
    )
    return OpenAIChatModel(model or settings.AI_DEFAULT_MODEL, provider=provider)


def build_agent(
    settings: Settings,
    *,
    model: str | None = None,
    system_prompt: str | Sequence[str] | None = None,
    deps_type: type[Any] | None = None,
    output_type: type[Any] | None = None,
    tools: Sequence[Any] | None = None,
    **agent_kwargs: Any,
) -> Agent[Any, Any]:
    """Build a Pydantic AI agent backed by the LLM Gateway.

    The kwargs forward straight through to :class:`pydantic_ai.Agent`.

    Args:
        settings: Application settings.
        model: Override the gateway model id (defaults to ``AI_DEFAULT_MODEL``).
        system_prompt: Static system prompt(s).
        deps_type: ``deps_type`` for typed dependency injection.
        output_type: ``output_type`` for structured Pydantic outputs.
        tools: Iterable of tools to register (functions or ``Tool`` objects).
        **agent_kwargs: Extra kwargs forwarded to ``Agent.__init__``.
    """
    from pydantic_ai import Agent

    chat_model = gateway_model(settings, model=model)

    kwargs: dict[str, Any] = dict(agent_kwargs)
    if system_prompt is not None:
        kwargs["system_prompt"] = system_prompt
    if deps_type is not None:
        kwargs["deps_type"] = deps_type
    if output_type is not None:
        kwargs["output_type"] = output_type
    if tools is not None:
        kwargs["tools"] = list(tools)

    return Agent(chat_model, **kwargs)


__all__ = (
    "GatewayNotConfiguredError",
    "build_agent",
    "gateway_model",
)
