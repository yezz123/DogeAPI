# DogeAPI

> Multi-tenant SaaS boilerplate built on FastAPI + [authx](https://github.com/yezz123/authx) + Next.js. Every feature toggleable via env vars; ship a production-ready SaaS in a weekend.

[![Backend](https://github.com/yezz123/DogeAPI/actions/workflows/backend.yml/badge.svg)](https://github.com/yezz123/DogeAPI/actions/workflows/backend.yml)
[![Frontend](https://github.com/yezz123/DogeAPI/actions/workflows/frontend.yml/badge.svg)](https://github.com/yezz123/DogeAPI/actions/workflows/frontend.yml)
[![Admin](https://github.com/yezz123/DogeAPI/actions/workflows/admin.yml/badge.svg)](https://github.com/yezz123/DogeAPI/actions/workflows/admin.yml)

## What you get

- **Organizations / Workspaces** with per-org data isolation (every tenant row carries `org_id`).
- **Roles**: Owner / Admin / Member, mapped to authx **scopes** with wildcard support (`org:members:*`).
- **JWT scoped to org** &mdash; switch orgs and the access token is re-issued with the new `org_id` and computed scopes.
- **API keys per organization** with scoped permissions, validated via `X-API-Key`.
- **Email invitations** &mdash; or token-link only when email delivery is disabled.
- Optional, all gated by `FEATURE_*` env vars: OAuth (Google/GitHub), magic-link, real email delivery (Resend/SMTP), Stripe billing, Pydantic AI chat via [fastapi-llm-gateway](https://pypi.org/project/fastapi-llm-gateway/), Logfire observability, audit log, rate limiting.

## Repository layout

```
DogeAPI/
├── backend/         FastAPI + authx + SQLAlchemy + Alembic (uv-managed)
├── frontend/        Next.js 15 tenant-facing app (Tailwind v4, Framer Motion, Zod)
├── admin/           Next.js 15 super-admin portal
├── infra/           docker-compose + postgres init
├── .env.sample      every FEATURE_* and secret in one place
└── Makefile         `make dev`, `make test`, `make migrate`, ...
```

## Stack

| Layer        | Tech                                                                                                                        |
| ------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Backend      | FastAPI, Pydantic v2, [authx](https://pypi.org/project/authx/) 1.6.0, SQLAlchemy 2 async, Alembic, Postgres 17, Redis 7, uv |
| Frontend     | Next.js 16, React 19, Tailwind v4, Framer Motion, Zod, bun                                                                  |
| Admin Portal | Next.js 16, React 19, Tailwind v4, Framer Motion, Zod, bun                                                                  |
| Optional     | Pydantic AI + fastapi-llm-gateway, Pydantic Logfire, Resend, Stripe, Authlib                                                |

## Quick start

Prereqs: **uv** &ge; 0.5, **bun** &ge; 1.3, **Docker**.

```bash
git clone https://github.com/yezz123/DogeAPI && cd DogeAPI
cp .env.sample .env

make bootstrap          # uv sync + bun install for all 3 apps
make up                 # postgres + redis + mailpit via docker compose
make migrate            # alembic upgrade head

# In three separate terminals:
make dev-backend        # http://localhost:8000  (FastAPI + /docs)
make dev-frontend       # http://localhost:3000  (tenant app)
make dev-admin          # http://localhost:3001  (super-admin)
```

## Feature flags

Every optional module is gated by an env var. Disabled features incur **zero**
runtime cost &mdash; their routers are never registered, their dependencies never
imported.

| Flag                     | Default | Module                            |
| ------------------------ | ------- | --------------------------------- |
| `FEATURE_API_KEYS`       | `true`  | API keys per org (`X-API-Key`)    |
| `FEATURE_AUDIT_LOG`      | `true`  | Audit log of mutations            |
| `FEATURE_RATE_LIMITING`  | `true`  | authx `RateLimiter` + Redis       |
| `FEATURE_OAUTH`          | `false` | Google + GitHub via Authlib       |
| `FEATURE_MAGIC_LINK`     | `false` | Passwordless                      |
| `FEATURE_EMAIL_DELIVERY` | `false` | Resend / SMTP                     |
| `FEATURE_AI_CHAT`        | `false` | Pydantic AI + fastapi-llm-gateway |
| `FEATURE_LOGFIRE`        | `false` | Pydantic Logfire tracing          |
| `FEATURE_STRIPE`         | `false` | Per-org subscriptions             |

Optional Python deps live behind `pyproject.toml` extras:

```bash
uv sync --extra ai --extra stripe       # only what you need
uv sync --extra all                     # everything
```

## Multi-tenancy model

- Shared database, shared schema. Every tenant row has `org_id UUID NOT NULL` with composite indexes.
- The active org lives in the JWT (`data.org_id` + `data.role` + `scopes`).
- `current_org` FastAPI dep extracts the org from the token and every repository function takes it as a required argument.
- `POST /orgs/{slug}/switch` re-issues the token pair with new claims.

## Roles &rarr; scopes

```python
ROLE_SCOPES = {
    Role.OWNER:  ["org:*"],
    Role.ADMIN:  ["org:members:*", "org:apikeys:*", "org:audit:read", "org:billing:read", "org:ai:*"],
    Role.MEMBER: ["org:read", "org:ai:use"],
}
```

Routes use `auth.scopes_required(...)` &mdash; wildcards (`"org:*"`) match
everything underneath.

## Development

See per-app READMEs:

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
- [admin/README.md](admin/README.md)

```bash
make test               # all suites
make lint               # ruff + next lint
make typecheck-backend  # mypy
```

## License

MIT &mdash; see [LICENSE](LICENSE).
