# syntax=docker/dockerfile:1.7
#
# Backend: FastAPI + uv. Multi-stage so the final image only carries the
# Python interpreter, the venv, and our source — no uv, no caches, no dev
# deps. Use BuildKit for the cache mounts.

ARG PYTHON_VERSION=3.12

# ─── Stage 1: base with uv ───────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=ghcr.io/astral-sh/uv:0.5.20 /uv /uvx /usr/local/bin/

WORKDIR /app

# ─── Stage 2: builder — install deps + project ───────────────────────────
FROM base AS builder

# System deps required by argon2-cffi, asyncpg, psycopg, etc.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies first (this layer is cached as long as the lock file
# doesn't change).
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --all-extras --no-dev

# Copy the project and install it into the venv. README.md is referenced
# from pyproject.toml so hatchling needs it during the build.
COPY README.md ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-extras --no-dev

# ─── Stage 3: runtime ────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Runtime libs only (no compilers).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 1001 app \
 && useradd --system --uid 1001 --gid app --home /app --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app src ./src

USER app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "dogeapi.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
