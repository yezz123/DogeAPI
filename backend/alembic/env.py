"""Alembic env.py for the AI Template backend.

Reads the DATABASE_URL_SYNC from app settings at runtime so migrations and
the application share a single source of truth.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from dogeapi.models import Base
from dogeapi.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Honour a programmatically-set URL (e.g. from tests) but otherwise fall
# back to the application settings so ``alembic upgrade head`` works as a
# CLI command without env hackery.
_current_url = config.get_main_option("sqlalchemy.url") or ""
if not _current_url or _current_url == "driver://user:pass@localhost/dbname":
    config.set_main_option("sqlalchemy.url", get_settings().DATABASE_URL_SYNC)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]
    """Hook to ignore objects we don't want autogen to track."""
    return True


def run_migrations_offline() -> None:
    """Generate SQL migration files without a live DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against the configured database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
