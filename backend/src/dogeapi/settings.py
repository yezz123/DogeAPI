"""Typed settings for AI Template.

Every feature flag here gates an entire module. The app factory in
:mod:`dogeapi.main` only registers a feature's router when the corresponding
``FEATURE_*`` flag is true, so disabled features incur zero runtime cost.

Optional Python dependencies live behind ``pyproject.toml`` extras; install
them with ``uv sync --extra ai`` etc., or ``uv sync --extra all`` for
everything.
"""

from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvName = Literal["development", "staging", "production", "test"]
EmailProvider = Literal["smtp", "resend"]


class Settings(BaseSettings):
    """Top-level application settings, sourced from env vars and ``.env``."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: EnvName = "development"
    APP_NAME: str = "AI Template"
    APP_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    ADMIN_BASE_URL: str = "http://localhost:3001"

    DATABASE_URL: str = "postgresql+asyncpg://dogeapi:dogeapi@localhost:5432/dogeapi"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://dogeapi:dogeapi@localhost:5432/dogeapi"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 20
    JWT_COOKIE_SECURE: bool = False
    JWT_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    FEATURE_API_KEYS: bool = True
    FEATURE_AUDIT_LOG: bool = True
    FEATURE_RATE_LIMITING: bool = True
    FEATURE_OAUTH: bool = False
    FEATURE_MAGIC_LINK: bool = False
    FEATURE_EMAIL_DELIVERY: bool = False
    FEATURE_AI_CHAT: bool = False
    FEATURE_LOGFIRE: bool = False
    FEATURE_STRIPE: bool = False
    FEATURE_HTTRACE: bool = False

    HTTRACE_API_KEY: str = ""
    HTTRACE_SERVICE: str = "ai-template"
    HTTRACE_SAMPLE_RATE: float = 0.1

    EMAIL_PROVIDER: EmailProvider = "smtp"
    EMAIL_FROM: str = "AI Template <noreply@dogeapi.local>"
    RESEND_API_KEY: str = ""
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False

    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: str = ""
    OAUTH_GITHUB_CLIENT_ID: str = ""
    OAUTH_GITHUB_CLIENT_SECRET: str = ""

    MAGIC_LINK_TTL_MINUTES: int = 15

    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_FREE: str = "price_free"
    STRIPE_PRICE_PRO: str = "price_pro"
    STRIPE_PRICE_ENTERPRISE: str = "price_enterprise"

    LLM_GATEWAY_URL: str = "https://api.llmgateway.io/v1"
    LLM_GATEWAY_API_KEY: str = ""
    AI_DEFAULT_MODEL: str = "gpt-5-mini"
    AI_MONTHLY_TOKEN_QUOTA: int = 1_000_000

    LOGFIRE_TOKEN: str = ""
    LOGFIRE_ENVIRONMENT: str = "development"

    RATE_LIMIT_PER_IP_PER_MINUTE: int = 60
    RATE_LIMIT_PER_USER_PER_MINUTE: int = 120
    RATE_LIMIT_PER_ORG_PER_MINUTE: int = 600
    RATE_LIMIT_PER_API_KEY_PER_MINUTE: int = 300

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwt_access_expires(self) -> timedelta:
        return timedelta(minutes=self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def jwt_refresh_expires(self) -> timedelta:
        return timedelta(days=self.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor.

    The cache makes settings effectively a singleton without paying the
    construction cost on every request. Call ``get_settings.cache_clear()``
    in tests to reload after env changes.
    """
    return Settings()


__all__ = ("EmailProvider", "EnvName", "Settings", "get_settings")
