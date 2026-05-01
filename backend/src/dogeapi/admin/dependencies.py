"""Super-admin authorisation dep."""

from __future__ import annotations

from fastapi import HTTPException, status

from dogeapi.deps import UserDep
from dogeapi.models import User


async def require_superadmin(user: UserDep) -> User:
    """Dep that rejects every non-superadmin caller."""
    if not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Super-admin required")
    return user
