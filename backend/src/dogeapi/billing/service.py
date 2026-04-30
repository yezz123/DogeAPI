"""Stripe service helpers.

The ``stripe`` SDK is imported lazily so it stays optional.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dogeapi.models import Organization, Subscription

if TYPE_CHECKING:
    from dogeapi.settings import Settings


def _stripe(settings: Settings):  # type: ignore[no-untyped-def]
    import stripe

    stripe.api_key = settings.STRIPE_API_KEY
    return stripe


_PRICE_ENV_KEYS = {
    "free": "STRIPE_PRICE_FREE",
    "pro": "STRIPE_PRICE_PRO",
    "enterprise": "STRIPE_PRICE_ENTERPRISE",
}


async def get_or_create_subscription(session: AsyncSession, org: Organization) -> Subscription:
    stmt = select(Subscription).where(Subscription.org_id == org.id)
    sub = (await session.execute(stmt)).scalar_one_or_none()
    if sub is not None:
        return sub
    sub = Subscription(org_id=org.id, plan=org.plan or "free", status="active")
    session.add(sub)
    await session.flush()
    return sub


async def create_checkout_session(
    session: AsyncSession,
    settings: Settings,
    *,
    org: Organization,
    plan: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Return a Stripe-hosted checkout URL for the given plan."""
    sub = await get_or_create_subscription(session, org)
    stripe = _stripe(settings)

    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(
            metadata={"org_id": str(org.id), "org_slug": org.slug},
            name=org.name,
        )
        sub.stripe_customer_id = customer.id
        await session.flush()

    price_id = getattr(settings, _PRICE_ENV_KEYS[plan])
    session_obj = stripe.checkout.Session.create(
        mode="subscription",
        customer=sub.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"org_id": str(org.id), "plan": plan},
    )
    return str(session_obj.url)


async def create_portal_session(
    session: AsyncSession,
    settings: Settings,
    *,
    org: Organization,
    return_url: str,
) -> str:
    sub = await get_or_create_subscription(session, org)
    if not sub.stripe_customer_id:
        return return_url

    stripe = _stripe(settings)
    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=return_url,
    )
    return str(portal.url)


async def apply_webhook_event(
    db_session: AsyncSession,
    event: dict[str, Any],
) -> None:
    """Update local state to mirror an incoming Stripe webhook event.

    Only handles the most common events; extend as needed.
    """
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    if event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
    }:
        customer_id = data.get("customer")
        subscription_id = data.get("id")
        status = data.get("status")
        period_end = data.get("current_period_end")
        plan_items = data.get("items", {}).get("data", [])
        plan = "free"
        if plan_items:
            nickname = plan_items[0].get("price", {}).get("nickname")
            if nickname:
                plan = nickname.lower()

        stmt = select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        sub = (await db_session.execute(stmt)).scalar_one_or_none()
        if sub is not None:
            sub.stripe_subscription_id = subscription_id
            sub.status = status or sub.status
            sub.plan = plan
            if period_end:
                sub.current_period_end = datetime.fromtimestamp(period_end, tz=UTC)
            await db_session.flush()

            org = await db_session.get(Organization, sub.org_id)
            if org is not None:
                org.plan = plan
                await db_session.flush()

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        stmt = select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        sub = (await db_session.execute(stmt)).scalar_one_or_none()
        if sub is not None:
            sub.status = "canceled"
            sub.plan = "free"
            await db_session.flush()


def _retrieve_user_id_for_org(_org_id: UUID) -> UUID | None:
    """Stub kept so future helpers can fan out a webhook to a user."""
    return None
