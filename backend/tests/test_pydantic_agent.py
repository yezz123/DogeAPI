"""Tests for the Pydantic AI integration on top of the LLM Gateway.

We mock the gateway over HTTP so the tests stay offline. Each test
verifies a different agent shape:

- ``build_agent`` raises when the gateway key is missing
- a structured-output agent parses Pydantic models from gateway JSON
- a tool-using agent dispatches to a Python function and returns text
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from dogeapi.ai.agents import GatewayNotConfiguredError, build_agent
from dogeapi.ai.examples import (
    ExtractedTask,
    build_concierge_agent,
    build_task_extractor,
)
from dogeapi.settings import Settings

GATEWAY_BASE = "https://api.llmgateway.io/v1"


def _settings(api_key: str = "test-key", base_url: str = GATEWAY_BASE) -> Settings:
    return Settings(
        JWT_SECRET_KEY="x" * 32,
        LLM_GATEWAY_URL=base_url,
        LLM_GATEWAY_API_KEY=api_key,
        AI_DEFAULT_MODEL="gpt-5-mini",
    )


# ─── Configuration guardrails ────────────────────────────────────────────


def test_build_agent_raises_when_no_gateway_key() -> None:
    settings = _settings(api_key="")
    with pytest.raises(GatewayNotConfiguredError):
        build_agent(settings, system_prompt="hello")


# ─── Structured output ───────────────────────────────────────────────────


@respx.mock
async def test_task_extractor_parses_structured_output() -> None:
    """The gateway's JSON tool-call payload must round-trip into ExtractedTask."""
    settings = _settings()

    payload_args = json.dumps(
        {
            "title": "Email Sarah about Q3 forecast",
            "description": "Reply with the Q3 forecast doc.",
            "due_iso": "2026-05-08",
            "priority": "high",
        }
    )

    respx.post(f"{GATEWAY_BASE}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "resp-1",
                "object": "chat.completion",
                "model": "gpt-5-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "final_result",
                                        "arguments": payload_args,
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 20,
                    "total_tokens": 70,
                    "cost": 0.0005,
                },
            },
        )
    )

    agent = build_task_extractor(settings)
    result = await agent.run("Email Sarah by Friday about the Q3 forecast — urgent")

    assert isinstance(result.output, ExtractedTask)
    assert result.output.title == "Email Sarah about Q3 forecast"
    assert result.output.priority == "high"
    assert result.output.due_iso == "2026-05-08"


# ─── Tool calling ────────────────────────────────────────────────────────


@respx.mock
async def test_concierge_agent_dispatches_to_python_tool() -> None:
    """The model asks for ``get_today_iso``; pydantic-ai dispatches and resumes."""
    settings = _settings()

    # First gateway call: model decides to call the tool.
    # Second gateway call: model produces the final answer using the tool result.
    responses = iter(
        [
            httpx.Response(
                200,
                json={
                    "id": "resp-tool-call",
                    "object": "chat.completion",
                    "created": 1_700_000_000,
                    "model": "gpt-5-mini",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "call_today",
                                        "type": "function",
                                        "function": {
                                            "name": "get_today_iso",
                                            "arguments": "{}",
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 4,
                        "total_tokens": 14,
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    "id": "resp-final",
                    "object": "chat.completion",
                    "created": 1_700_000_010,
                    "model": "gpt-5-mini",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "Today is the date the tool returned.",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 20,
                        "completion_tokens": 12,
                        "total_tokens": 32,
                    },
                },
            ),
        ]
    )

    def _route(_request: httpx.Request) -> httpx.Response:
        return next(responses)

    respx.post(f"{GATEWAY_BASE}/chat/completions").mock(side_effect=_route)

    from dogeapi.ai.examples import WeatherSummary

    agent = build_concierge_agent(settings)
    result = await agent.run(
        "What is today?",
        deps=WeatherSummary(units="celsius"),
    )
    assert "Today" in result.output


# ─── Generic build_agent shape ──────────────────────────────────────────


@respx.mock
async def test_build_agent_returns_plain_text_by_default() -> None:
    settings = _settings()
    respx.post(f"{GATEWAY_BASE}/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "resp-plain",
                "object": "chat.completion",
                "created": 1_700_000_000,
                "model": "gpt-5-mini",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hi back"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 2,
                    "total_tokens": 3,
                },
            },
        )
    )

    agent = build_agent(settings, system_prompt="be concise")
    result = await agent.run("hi")
    assert result.output == "hi back"


# ─── Custom base URL plumbing ────────────────────────────────────────────


def test_gateway_model_uses_configured_base_url() -> None:
    settings = _settings(base_url="http://localhost:4000/v1")
    from dogeapi.ai.agents import gateway_model

    model = gateway_model(settings)
    # OpenAIChatModel exposes `base_url` on the underlying client config.
    client = model.client  # type: ignore[attr-defined]
    assert "localhost:4000" in str(client.base_url)
