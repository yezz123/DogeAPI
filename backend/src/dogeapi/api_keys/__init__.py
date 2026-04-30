"""API keys: per-org tokens that can replace JWTs for machine clients.

Module is gated by ``settings.FEATURE_API_KEYS``; when off, the router is
not registered and the X-API-Key dependency rejects every request.
"""

from dogeapi.api_keys.dependencies import (
    api_key_or_jwt_payload,
    require_api_key_scope,
    require_jwt_or_api_key_scope,
)
from dogeapi.api_keys.router import router

__all__ = (
    "api_key_or_jwt_payload",
    "require_api_key_scope",
    "require_jwt_or_api_key_scope",
    "router",
)
