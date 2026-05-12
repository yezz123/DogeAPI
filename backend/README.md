# Backend

FastAPI + authx-powered backend for the AI Template multi-tenant SaaS boilerplate.

## Quick start

```bash
uv sync
cp ../.env.example ../.env
docker compose -f ../infra/docker-compose.yml up -d postgres redis mailpit
uv run alembic upgrade head
uv run dogeapi admin create --email admin@example.com --password change-me-admin-password
uv run uvicorn dogeapi.main:app --reload
```

Visit `http://localhost:8000/docs` for the OpenAPI UI. Use `/healthz` for
liveness and `/readyz` for deployment readiness checks against Postgres and
Redis.

For the full Docker stack, run commands from the repository root through
`make stack-up`. That path loads `.env` and starts the Nginx gateway at
`http://localhost:8080`.

## Development

```bash
uv run pytest                    # run tests
uv run ruff check .              # lint
uv run ruff format .             # format
uv run mypy src                  # type-check
uv run alembic revision --autogenerate -m "description"
uv run dogeapi admin create --email admin@example.com --password change-me-admin-password
```

The admin bootstrap command is idempotent: it creates the user if missing, or
promotes and verifies the existing user. Pass `--update-password` when you want
to rotate an existing admin password.

## Architecture

See the root [README](../README.md) and the plan document.

Each feature module under `src/dogeapi/` is wired into `main.py` only when
its `FEATURE_*` env var is `true`. Optional Python dependencies live behind
`pyproject.toml` extras (`email`, `oauth`, `ai`, `stripe`, `logfire`).

Production settings fail fast when placeholder secrets, insecure cookies, or
enabled integrations without required secrets are detected.

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
