# Backend

FastAPI + authx-powered backend for the AI Template multi-tenant SaaS boilerplate.

## Quick start

```bash
uv sync
cp ../.env.sample ../.env
docker compose -f ../infra/docker-compose.yml up -d postgres redis mailpit
uv run alembic upgrade head
uv run uvicorn dogeapi.main:app --reload
```

Visit `http://localhost:8000/docs` for the OpenAPI UI.

## Development

```bash
uv run pytest                    # run tests
uv run ruff check .              # lint
uv run ruff format .             # format
uv run mypy src                  # type-check
uv run alembic revision --autogenerate -m "description"
```

## Architecture

See the root [README](../README.md) and the plan document.

Each feature module under `src/dogeapi/` is wired into `main.py` only when
its `FEATURE_*` env var is `true`. Optional Python dependencies live behind
`pyproject.toml` extras (`email`, `oauth`, `ai`, `stripe`, `logfire`).

```
src/dogeapi/
├── main.py            # app factory; conditional router include
├── settings.py        # FEATURE_* flags + secrets
├── deps.py            # FastAPI deps (db, redis, auth, current_user, current_org)
├── auth/              # authx wiring + register/login/refresh/logout
├── organizations/     # orgs, memberships, invitations, RBAC
├── api_keys/          # X-API-Key auth (optional)
├── audit_log/         # mutation logging (optional)
├── rate_limit/        # authx RateLimiter + Redis (optional)
├── oauth/             # Authlib Google/GitHub (optional)
├── magic_link/        # passwordless (optional)
├── email/             # Resend / SMTP adapter
├── billing/           # Stripe (optional)
├── ai/                # Pydantic AI + LLM gateway (optional)
├── observability/     # Logfire (optional)
├── admin/             # super-admin endpoints
└── models/            # SQLAlchemy ORM
```
