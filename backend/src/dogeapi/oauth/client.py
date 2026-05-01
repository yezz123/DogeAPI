"""Authlib OAuth client factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from authlib.integrations.starlette_client import OAuth

    from dogeapi.settings import Settings


def build_oauth(settings: Settings) -> OAuth:
    """Construct an Authlib ``OAuth`` registry from app settings.

    Only providers whose client id and secret are present are registered.
    """
    from authlib.integrations.starlette_client import OAuth

    oauth = OAuth()

    if settings.OAUTH_GOOGLE_CLIENT_ID and settings.OAUTH_GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=settings.OAUTH_GOOGLE_CLIENT_ID,
            client_secret=settings.OAUTH_GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    if settings.OAUTH_GITHUB_CLIENT_ID and settings.OAUTH_GITHUB_CLIENT_SECRET:
        oauth.register(
            name="github",
            client_id=settings.OAUTH_GITHUB_CLIENT_ID,
            client_secret=settings.OAUTH_GITHUB_CLIENT_SECRET,
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email"},
        )

    return oauth
