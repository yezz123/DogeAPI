"""Per-org monthly AI token quota using a Redis counter.

Key shape: ``ai_quota:{org_id}:{YYYY-MM}``. The counter is reserved
*before* the LLM call (max possible tokens) and refunded after with the
actual usage; this keeps over-spend impossible while keeping accounting
honest.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from redis.asyncio import Redis

PREFIX = "ai_quota:"
SECONDS_IN_35_DAYS = 60 * 60 * 24 * 35


def _key(org_id: UUID) -> str:
    today = datetime.now(UTC)
    return f"{PREFIX}{org_id}:{today:%Y-%m}"


async def monthly_usage(redis: Redis, org_id: UUID) -> int:
    raw = await redis.get(_key(org_id))
    if not raw:
        return 0
    return int(raw.decode("utf-8") if isinstance(raw, bytes) else raw)


async def check_and_reserve(
    redis: Redis,
    org_id: UUID,
    *,
    estimate: int,
    limit: int | None,
) -> bool:
    """Atomically reserve ``estimate`` tokens for this org.

    Returns ``True`` on success; ``False`` if doing so would exceed ``limit``
    (in which case nothing is reserved).
    """
    if limit is None:
        await redis.incrby(_key(org_id), estimate)
        return True

    new_total = int(await redis.incrby(_key(org_id), estimate))
    await redis.expire(_key(org_id), SECONDS_IN_35_DAYS, nx=True)

    if new_total > limit:
        await redis.decrby(_key(org_id), estimate)
        return False
    return True


async def refund(redis: Redis, org_id: UUID, *, delta: int) -> None:
    """Adjust the counter by ``delta`` (negative = refund).

    Use the actual tokens consumed minus the original estimate.
    """
    if delta == 0:
        return
    if delta > 0:
        await redis.incrby(_key(org_id), delta)
    else:
        await redis.decrby(_key(org_id), -delta)
