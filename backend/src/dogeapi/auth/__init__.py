"""Auth module: authx wiring + register/login/refresh/logout/me/email-verify.

The whole module is always-on; toggling email delivery only changes whether
verification mails are *sent* &mdash; the verify endpoints still exist.
"""

from dogeapi.auth.router import router
from dogeapi.auth.security import build_authx, get_authx

__all__ = ("build_authx", "get_authx", "router")
