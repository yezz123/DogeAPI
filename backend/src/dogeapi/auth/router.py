"""Auth endpoints: register / login / refresh / logout / me / verify-email."""

from __future__ import annotations

from authx import TokenPayload
from fastapi import APIRouter, HTTPException, Request, Response, status

from dogeapi.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    TokenPairResponse,
    UserResponse,
    VerifyEmailRequest,
)
from dogeapi.auth.service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate,
    mark_email_verified,
    register_user,
)
from dogeapi.auth.tokens import consume_email_verify_token, issue_email_verify_token
from dogeapi.deps import AuthDep, RedisDep, SessionDep, SettingsDep, TokenDep, UserDep

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_pair(auth: AuthDep, user_id: str) -> TokenPairResponse:
    pair = auth.create_token_pair(uid=user_id, fresh=True)
    return TokenPairResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    response: Response,
    session: SessionDep,
    redis: RedisDep,
    auth: AuthDep,
    settings: SettingsDep,
) -> RegisterResponse:
    """Create a new user, issue tokens, and seed an email verification token.

    When ``FEATURE_EMAIL_DELIVERY`` is off the verification link is returned
    in the response body so a developer can complete signup without an SMTP
    server. When email delivery is on the link is sent by mail and not echoed.
    """
    try:
        user = await register_user(
            session,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered") from exc

    tokens = _token_pair(auth, str(user.id))
    auth.set_access_cookies(tokens.access_token, response)
    auth.set_refresh_cookies(tokens.refresh_token, response)

    verify_token = await issue_email_verify_token(redis, user.id)
    verify_link = f"{settings.FRONTEND_BASE_URL}/verify-email?token={verify_token}"

    payload_link: str | None = None
    if not settings.FEATURE_EMAIL_DELIVERY:
        payload_link = verify_link
    else:
        from dogeapi.email import send_email_verification

        await send_email_verification(settings, to=user.email, link=verify_link)

    return RegisterResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
        email_verification_link=payload_link,
    )


@router.post("/login", response_model=TokenPairResponse)
async def login(
    body: LoginRequest,
    response: Response,
    session: SessionDep,
    auth: AuthDep,
) -> TokenPairResponse:
    try:
        user = await authenticate(session, email=body.email, password=body.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password") from exc

    tokens = _token_pair(auth, str(user.id))
    auth.set_access_cookies(tokens.access_token, response)
    auth.set_refresh_cookies(tokens.refresh_token, response)
    return tokens


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(
    request: Request,
    response: Response,
    auth: AuthDep,
) -> TokenPairResponse:
    """Exchange a refresh token for a fresh access+refresh pair."""
    payload: TokenPayload = await auth.refresh_token_required(request=request)
    user_id = str(payload.sub)
    pair = auth.create_token_pair(uid=user_id, fresh=False)
    auth.set_access_cookies(pair.access_token, response)
    auth.set_refresh_cookies(pair.refresh_token, response)
    return TokenPairResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    auth: AuthDep,
    redis: RedisDep,
    payload: TokenDep,
) -> MessageResponse:
    """Revoke the current access token via Redis blocklist and clear cookies.

    The blocklist key TTL matches the token's remaining lifetime, so we
    never accumulate stale entries.
    """
    auth.unset_cookies(response)

    raw_request_token = await auth.get_token_from_request(request, type="access", optional=True)
    if raw_request_token is not None:
        ttl = max(int(payload.time_until_expiry.total_seconds()), 1)
        await redis.setex(f"blocklist:{raw_request_token.token}", ttl, "1")

    return MessageResponse(detail="Logged out")


@router.get("/me", response_model=UserResponse)
async def me(user: UserDep) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    body: VerifyEmailRequest,
    session: SessionDep,
    redis: RedisDep,
) -> MessageResponse:
    user_id = await consume_email_verify_token(redis, body.token)
    if user_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Invalid or expired verification token",
        )
    await mark_email_verified(session, user_id)
    return MessageResponse(detail="Email verified")
