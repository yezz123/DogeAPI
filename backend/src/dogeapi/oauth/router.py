"""OAuth router: ``/auth/oauth/{provider}/start`` + ``/callback``."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Request, status
from fastapi.responses import RedirectResponse

from dogeapi.deps import AuthDep, SessionDep, SettingsDep
from dogeapi.oauth.service import upsert_user_from_oauth

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])


def _oauth(request: Request) -> Any:
    """Pull the per-app Authlib OAuth registry off ``app.state``."""
    oauth = getattr(request.app.state, "oauth", None)
    if oauth is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "OAuth not configured on this server",
        )
    return oauth


@router.get("/{provider}/start")
async def start(
    request: Request,
    settings: SettingsDep,
    provider: Annotated[str, Path(min_length=1)],
) -> RedirectResponse:
    oauth = _oauth(request)
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown OAuth provider")
    redirect_uri = f"{settings.APP_BASE_URL}/auth/oauth/{provider}/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback")
async def callback(
    request: Request,
    session: SessionDep,
    auth: AuthDep,
    settings: SettingsDep,
    provider: Annotated[str, Path(min_length=1)],
) -> RedirectResponse:
    oauth = _oauth(request)
    client = oauth.create_client(provider)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown OAuth provider")

    try:
        token = await client.authorize_access_token(request)
    except Exception as exc:  # pragma: no cover  - oauth lib raises various
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "OAuth callback failed") from exc

    if provider == "google":
        userinfo = token.get("userinfo") or await client.userinfo(token=token)
        provider_account_id = str(userinfo["sub"])
        email = userinfo["email"]
        full_name = userinfo.get("name")
    elif provider == "github":
        resp = await client.get("user", token=token)
        data = resp.json()
        provider_account_id = str(data["id"])
        email = data.get("email")
        if not email:
            emails_resp = await client.get("user/emails", token=token)
            for entry in emails_resp.json():
                if entry.get("primary") and entry.get("verified"):
                    email = entry["email"]
                    break
        if not email:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No verified email on GitHub")
        full_name = data.get("name")
    else:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown OAuth provider")

    user = await upsert_user_from_oauth(
        session,
        provider=provider,
        provider_account_id=provider_account_id,
        email=email,
        full_name=full_name,
    )

    pair = auth.create_token_pair(uid=str(user.id), fresh=True)
    response = RedirectResponse(url=f"{settings.FRONTEND_BASE_URL}/dashboard")
    auth.set_access_cookies(pair.access_token, response)
    auth.set_refresh_cookies(pair.refresh_token, response)
    return response
