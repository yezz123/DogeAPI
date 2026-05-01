"""Email delivery adapter.

Imports are kept lazy so the ``email`` extra (resend, aiosmtplib) is only
required when ``FEATURE_EMAIL_DELIVERY`` is true.
"""

from __future__ import annotations

from dogeapi.email.adapter import (
    NoopMailer,
    ResendMailer,
    SMTPMailer,
    build_mailer,
    send_email_verification,
    send_invitation_email,
    send_magic_link,
    send_password_reset,
)

__all__ = (
    "NoopMailer",
    "ResendMailer",
    "SMTPMailer",
    "build_mailer",
    "send_email_verification",
    "send_invitation_email",
    "send_magic_link",
    "send_password_reset",
)
