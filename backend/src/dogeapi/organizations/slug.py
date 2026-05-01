"""Slug utilities for organizations."""

from __future__ import annotations

import re
import secrets

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Best-effort slugify (ASCII-only)."""
    base = _SLUG_RE.sub("-", value.strip().lower()).strip("-")
    if not base:
        base = "org"
    return base[:48]


def random_suffix(length: int = 5) -> str:
    return secrets.token_hex(length)[:length]
