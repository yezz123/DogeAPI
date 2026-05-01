"""Argon2id password hashing.

We isolate the hasher behind a tiny module so we can swap algorithms or
parameters in one place.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Returns False on mismatch instead of raising, since callers virtually
    always want a boolean.
    """
    try:
        _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    return True


def needs_rehash(hashed: str) -> bool:
    """Should the stored hash be upgraded with current parameters?"""
    return _hasher.check_needs_rehash(hashed)
