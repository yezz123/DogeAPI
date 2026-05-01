"""Per-plan limits.

Other modules consult :func:`get_plan_limits` to enforce caps such as
"max API keys per org" or "monthly AI tokens." A value of ``None`` means
unlimited.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlanLimits:
    plan: str
    max_members: int | None
    max_api_keys: int | None
    monthly_ai_tokens: int | None


PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(
        plan="free",
        max_members=5,
        max_api_keys=2,
        monthly_ai_tokens=100_000,
    ),
    "pro": PlanLimits(
        plan="pro",
        max_members=50,
        max_api_keys=20,
        monthly_ai_tokens=2_000_000,
    ),
    "enterprise": PlanLimits(
        plan="enterprise",
        max_members=None,
        max_api_keys=None,
        monthly_ai_tokens=None,
    ),
}


def get_plan_limits(plan: str) -> PlanLimits:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
