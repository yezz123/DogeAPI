"""Billing router: checkout, portal, webhook."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.billing import service
from dogeapi.billing.limits import PLAN_LIMITS, PlanLimits, get_plan_limits
from dogeapi.db import get_session
from dogeapi.deps import SessionDep, SettingsDep
from dogeapi.models import Subscription
from dogeapi.security import OrgMatch, require_scope

logger = logging.getLogger(__name__)
router = APIRouter(tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: str  # "pro" or "enterprise"


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: str | None
    limits: dict[str, int | None]


@router.get(
    "/orgs/{slug}/billing/subscription",
    response_model=SubscriptionResponse,
    dependencies=[Depends(require_scope("org:billing:read"))],
)
async def get_subscription(
    org: OrgMatch,
    session: SessionDep,
) -> SubscriptionResponse:
    sub = await service.get_or_create_subscription(session, org)
    limits: PlanLimits = get_plan_limits(sub.plan)
    return SubscriptionResponse(
        plan=sub.plan,
        status=sub.status,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
        limits={
            "max_members": limits.max_members,
            "max_api_keys": limits.max_api_keys,
            "monthly_ai_tokens": limits.monthly_ai_tokens,
        },
    )


@router.post(
    "/orgs/{slug}/billing/checkout",
    response_model=CheckoutResponse,
    dependencies=[Depends(require_scope("org:billing:write"))],
)
async def create_checkout(
    body: CheckoutRequest,
    org: OrgMatch,
    session: SessionDep,
    settings: SettingsDep,
) -> CheckoutResponse:
    if body.plan not in PLAN_LIMITS or body.plan == "free":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid plan")
    if not settings.STRIPE_API_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Stripe not configured",
        )

    success_url = f"{settings.FRONTEND_BASE_URL}/orgs/{org.slug}/settings?checkout=success"
    cancel_url = f"{settings.FRONTEND_BASE_URL}/orgs/{org.slug}/settings?checkout=cancel"
    url = await service.create_checkout_session(
        session,
        settings,
        org=org,
        plan=body.plan,
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return CheckoutResponse(url=url)


@router.post(
    "/orgs/{slug}/billing/portal",
    response_model=PortalResponse,
    dependencies=[Depends(require_scope("org:billing:write"))],
)
async def open_portal(
    org: OrgMatch,
    session: SessionDep,
    settings: SettingsDep,
) -> PortalResponse:
    if not settings.STRIPE_API_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Stripe not configured",
        )
    return_url = f"{settings.FRONTEND_BASE_URL}/orgs/{org.slug}/settings"
    url = await service.create_portal_session(session, settings, org=org, return_url=return_url)
    return PortalResponse(url=url)


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    settings: SettingsDep,
    db_session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    """Receive Stripe webhook events.

    Verifies the signature and applies the event to local state. Always
    returns 200 even on unhandled events to keep the Stripe retry queue
    short.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Stripe webhooks not configured",
        )

    import stripe

    body = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(body, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Invalid webhook signature",
        ) from exc

    await service.apply_webhook_event(db_session, dict(event))
    return {"status": "ok"}


@router.get(
    "/orgs/{slug}/billing/usage",
    dependencies=[Depends(require_scope("org:billing:read"))],
)
async def get_usage(org: OrgMatch, session: SessionDep) -> dict[str, int]:
    """Lightweight usage snapshot for plan-limit UI."""
    from dogeapi.models import APIKey, Membership

    members = await session.execute(select(Membership).where(Membership.org_id == org.id))
    api_keys = await session.execute(select(APIKey).where(APIKey.org_id == org.id))
    return {
        "members": len(members.scalars().all()),
        "api_keys": len(api_keys.scalars().all()),
    }


__all__ = ("Subscription", "router")
