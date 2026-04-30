"""Pydantic Logfire setup (FEATURE_LOGFIRE).

The :func:`setup_logfire` function is called from :mod:`dogeapi.main` when
``FEATURE_LOGFIRE`` is true *and* ``LOGFIRE_TOKEN`` is set. Importing this
module is safe even without the ``logfire`` extra installed; the actual
``import logfire`` happens inside the function and is caught by the caller.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from dogeapi.settings import Settings


def setup_logfire(app: FastAPI, settings: Settings) -> None:
    """Configure Logfire and instrument FastAPI + SQLAlchemy + Redis + httpx.

    Raises :class:`ImportError` if the ``logfire`` extra isn't installed.
    """
    import logfire

    logfire.configure(
        token=settings.LOGFIRE_TOKEN,
        environment=settings.LOGFIRE_ENVIRONMENT,
        service_name=settings.APP_NAME,
        service_version=app.version,
        send_to_logfire="if-token-present",
    )

    logfire.instrument_fastapi(app)

    with contextlib.suppress(Exception):
        logfire.instrument_httpx()

    with contextlib.suppress(Exception):
        from dogeapi.db import get_engine

        engine = get_engine()
        logfire.instrument_sqlalchemy(engine=engine.sync_engine)  # type: ignore[arg-type]

    with contextlib.suppress(Exception):
        logfire.instrument_redis()


__all__ = ("setup_logfire",)
