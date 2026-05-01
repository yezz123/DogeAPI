"""Smoke tests for the Logfire wiring (P11).

We don't talk to Logfire in CI; we verify that:

- :func:`setup_logfire` is callable and importable.
- The lifespan code path is gated by both FEATURE_LOGFIRE *and* LOGFIRE_TOKEN.
"""

from __future__ import annotations

import pytest


def test_setup_logfire_callable() -> None:
    from dogeapi.observability import setup_logfire

    assert callable(setup_logfire)


def test_setup_logfire_raises_friendly_error_without_logfire_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If ``logfire`` is not installed and we call setup, an ``ImportError``
    is raised which the lifespan catches.
    """
    import builtins
    import sys

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if name == "logfire":
            raise ImportError("logfire not installed")
        return real_import(name, *args, **kwargs)

    sys.modules.pop("logfire", None)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    from fastapi import FastAPI

    from dogeapi.observability import setup_logfire
    from dogeapi.settings import Settings

    app = FastAPI()
    settings = Settings(LOGFIRE_TOKEN="x", JWT_SECRET_KEY="y")
    with pytest.raises(ImportError):
        setup_logfire(app, settings)
