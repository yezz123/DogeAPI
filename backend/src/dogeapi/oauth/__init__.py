"""OAuth module: Authlib-backed Google + GitHub sign-in.

Imported lazily by the app factory only when ``FEATURE_OAUTH`` is true so
the ``authlib`` extra stays optional.
"""

from dogeapi.oauth.client import build_oauth
from dogeapi.oauth.router import router

__all__ = ("build_oauth", "router")
