"""HTTP exception handlers for authx errors and friends.

We map authx token errors onto canonical 401/403/429 responses with a
consistent JSON body.
"""

from __future__ import annotations

from authx.exceptions import (
    AuthXException,
    CSRFError,
    InsufficientScopeError,
    JWTDecodeError,
    MissingTokenError,
    RateLimitExceeded,
    RevokedTokenError,
    TokenError,
)
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


def _err(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def install_exception_handlers(app: FastAPI) -> None:
    """Register authx exception handlers on the given FastAPI app."""

    @app.exception_handler(MissingTokenError)
    async def _missing(_request: Request, exc: MissingTokenError) -> JSONResponse:
        return _err(status.HTTP_401_UNAUTHORIZED, "Authentication required")

    @app.exception_handler(RevokedTokenError)
    async def _revoked(_request: Request, exc: RevokedTokenError) -> JSONResponse:
        return _err(status.HTTP_401_UNAUTHORIZED, "Token revoked")

    @app.exception_handler(JWTDecodeError)
    async def _decode(_request: Request, exc: JWTDecodeError) -> JSONResponse:
        return _err(status.HTTP_401_UNAUTHORIZED, str(exc) or "Invalid token")

    @app.exception_handler(InsufficientScopeError)
    async def _scope(_request: Request, exc: InsufficientScopeError) -> JSONResponse:
        return _err(status.HTTP_403_FORBIDDEN, "Insufficient scope")

    @app.exception_handler(CSRFError)
    async def _csrf(_request: Request, exc: CSRFError) -> JSONResponse:
        return _err(status.HTTP_403_FORBIDDEN, str(exc) or "CSRF check failed")

    @app.exception_handler(RateLimitExceeded)
    async def _rate(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return _err(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests")

    @app.exception_handler(TokenError)
    async def _token(_request: Request, exc: TokenError) -> JSONResponse:
        return _err(status.HTTP_401_UNAUTHORIZED, str(exc) or "Authentication error")

    @app.exception_handler(AuthXException)
    async def _authx_fallback(_request: Request, exc: AuthXException) -> JSONResponse:
        return _err(status.HTTP_401_UNAUTHORIZED, str(exc) or "Authentication error")
