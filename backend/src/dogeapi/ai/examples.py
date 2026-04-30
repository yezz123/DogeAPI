"""Example Pydantic AI agents.

These are concrete, runnable examples that demonstrate how to build typed
agents on top of the LLM Gateway. They aren't auto-registered as routes;
copy or import them into your own modules.

Run with:

    from dogeapi.ai.examples import build_task_extractor
    from dogeapi.settings import get_settings

    agent = build_task_extractor(get_settings())
    result = await agent.run("Email Sarah by Friday about the Q3 forecast")
    print(result.output)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

from dogeapi.ai.agents import build_agent

if TYPE_CHECKING:
    from pydantic_ai import Agent

    from dogeapi.settings import Settings


# ─── Example 1: structured output ────────────────────────────────────────


class ExtractedTask(BaseModel):
    """A single actionable task extracted from free-form text."""

    title: str = Field(description="Short imperative title (verb-first).")
    description: str | None = Field(default=None, description="Optional 1-sentence elaboration.")
    due_iso: str | None = Field(
        default=None,
        description="ISO-8601 date or datetime if a deadline was mentioned.",
    )
    priority: Literal["low", "medium", "high"] = Field(default="medium", description="Triage priority.")


def build_task_extractor(settings: Settings) -> Agent[None, ExtractedTask]:
    """Agent that converts a sentence into a structured :class:`ExtractedTask`."""
    return build_agent(
        settings,
        system_prompt=(
            "You convert messages into a single actionable task. "
            "Return exactly one task; never ask follow-up questions."
        ),
        output_type=ExtractedTask,
    )


# ─── Example 2: agent with a tool ────────────────────────────────────────


class WeatherSummary(BaseModel):
    """Tiny demo deps payload."""

    units: Literal["celsius", "fahrenheit"] = "celsius"


def build_concierge_agent(settings: Settings) -> Agent[WeatherSummary, str]:
    """Agent that can call ``get_today_iso`` to ground its replies in time.

    Useful for demonstrating tool-calling without any external services.
    """
    agent = build_agent(
        settings,
        deps_type=WeatherSummary,
        system_prompt=(
            "You are a friendly concierge for a multi-tenant SaaS. Use the available tools when freshness matters."
        ),
    )

    @agent.tool_plain
    def get_today_iso() -> str:
        """Return today's date in ISO-8601 (UTC)."""
        return datetime.now(UTC).date().isoformat()

    return agent


__all__ = (
    "ExtractedTask",
    "WeatherSummary",
    "build_concierge_agent",
    "build_task_extractor",
)
