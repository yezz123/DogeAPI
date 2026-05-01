"""Pluggable email backends.

The default :class:`NoopMailer` is used whenever ``FEATURE_EMAIL_DELIVERY``
is false: it logs the email and discards it. Real backends (:class:`SMTPMailer`,
:class:`ResendMailer`) are constructed lazily so missing optional deps don't
break the import.
"""

from __future__ import annotations

import logging
from typing import Protocol

from dogeapi.settings import Settings

logger = logging.getLogger(__name__)


class Mailer(Protocol):
    """Pluggable mailer interface."""

    async def send(self, *, to: str, subject: str, html: str, text: str | None = None) -> None: ...


class NoopMailer:
    """Mailer that just logs &mdash; perfect for tests + dev w/o SMTP."""

    async def send(self, *, to: str, subject: str, html: str, text: str | None = None) -> None:
        logger.info("Email (noop) to=%s subject=%r", to, subject)


class SMTPMailer:
    """Async SMTP mailer using aiosmtplib."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send(self, *, to: str, subject: str, html: str, text: str | None = None) -> None:
        try:
            from email.message import EmailMessage

            import aiosmtplib
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install the 'email' extra: uv sync --extra email") from exc

        message = EmailMessage()
        message["From"] = self.settings.EMAIL_FROM
        message["To"] = to
        message["Subject"] = subject
        if text:
            message.set_content(text)
        message.add_alternative(html, subtype="html")

        await aiosmtplib.send(
            message,
            hostname=self.settings.SMTP_HOST,
            port=self.settings.SMTP_PORT,
            username=self.settings.SMTP_USER or None,
            password=self.settings.SMTP_PASSWORD or None,
            use_tls=self.settings.SMTP_USE_TLS,
        )


class ResendMailer:
    """Resend HTTP API mailer."""

    def __init__(self, settings: Settings):
        if not settings.RESEND_API_KEY:
            raise RuntimeError("RESEND_API_KEY is not set")
        self.settings = settings

    async def send(self, *, to: str, subject: str, html: str, text: str | None = None) -> None:
        try:
            import resend
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install the 'email' extra: uv sync --extra email") from exc

        resend.api_key = self.settings.RESEND_API_KEY
        params: dict[str, object] = {
            "from": self.settings.EMAIL_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if text:
            params["text"] = text
        resend.Emails.send(params)  # type: ignore[arg-type]


def build_mailer(settings: Settings) -> Mailer:
    """Construct the mailer matching configured settings."""
    if not settings.FEATURE_EMAIL_DELIVERY:
        return NoopMailer()
    if settings.EMAIL_PROVIDER == "resend":
        return ResendMailer(settings)
    return SMTPMailer(settings)


# ─── Convenience wrappers used by feature modules ─────────────────────────


async def send_email_verification(settings: Settings, *, to: str, link: str) -> None:
    mailer = build_mailer(settings)
    html = f"""
    <h1>Confirm your email</h1>
    <p>Click the link below to confirm your email for {settings.APP_NAME}:</p>
    <p><a href="{link}">{link}</a></p>
    <p>If you didn't create an account, ignore this email.</p>
    """
    text = f"Confirm your email at: {link}"
    await mailer.send(to=to, subject=f"Confirm your {settings.APP_NAME} account", html=html, text=text)


async def send_invitation_email(settings: Settings, *, to: str, org_name: str, link: str) -> None:
    mailer = build_mailer(settings)
    html = f"""
    <h1>You're invited to {org_name} on {settings.APP_NAME}</h1>
    <p>Accept the invitation by following this link:</p>
    <p><a href="{link}">{link}</a></p>
    """
    text = f"You're invited to {org_name}. Accept at: {link}"
    await mailer.send(to=to, subject=f"You're invited to {org_name}", html=html, text=text)


async def send_magic_link(settings: Settings, *, to: str, link: str) -> None:
    mailer = build_mailer(settings)
    html = f"""
    <h1>Sign in to {settings.APP_NAME}</h1>
    <p>Click the link below to sign in. It expires in {settings.MAGIC_LINK_TTL_MINUTES} minutes.</p>
    <p><a href="{link}">{link}</a></p>
    """
    await mailer.send(to=to, subject=f"Sign in to {settings.APP_NAME}", html=html, text=f"Sign in: {link}")


async def send_password_reset(settings: Settings, *, to: str, link: str) -> None:
    mailer = build_mailer(settings)
    html = f"""
    <h1>Reset your password</h1>
    <p>Click below to reset. If you didn't request this, ignore this email.</p>
    <p><a href="{link}">{link}</a></p>
    """
    await mailer.send(to=to, subject=f"Reset your {settings.APP_NAME} password", html=html, text=f"Reset: {link}")
