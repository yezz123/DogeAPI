"""AI chat module (FEATURE_AI_CHAT).

Wraps Pydantic AI's ``Agent`` with per-org quota enforcement and
threads/messages persistence.
"""

from dogeapi.ai.quota import check_and_reserve, monthly_usage, refund
from dogeapi.ai.router import router

__all__ = ("check_and_reserve", "monthly_usage", "refund", "router")
