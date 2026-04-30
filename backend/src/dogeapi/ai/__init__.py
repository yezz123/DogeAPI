"""AI chat module (FEATURE_AI_CHAT).

Two layers:

- The thread/message *chat* flow uses raw httpx against the LLM Gateway
  (``dogeapi.ai.gateway``) for fast, low-overhead chat completions.
- The *agent* layer (``dogeapi.ai.agents``) wraps Pydantic AI on top of
  the same gateway, giving you typed structured outputs, tools, and
  multi-step workflows. See :mod:`dogeapi.ai.examples`.

Both layers honour :class:`dogeapi.settings.Settings.LLM_GATEWAY_API_KEY`
&mdash; no key, no calls, and the chat layer falls back to a deterministic
echo agent for offline dev.
"""

from dogeapi.ai.quota import check_and_reserve, monthly_usage, refund
from dogeapi.ai.router import router

__all__ = ("check_and_reserve", "monthly_usage", "refund", "router")
