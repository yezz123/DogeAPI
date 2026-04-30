.DEFAULT_GOAL := help
SHELL := /usr/bin/env bash

# ─── Helpers ──────────────────────────────────────────────────────────────
.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ─── Bootstrap ────────────────────────────────────────────────────────────
.PHONY: bootstrap
bootstrap: bootstrap-backend bootstrap-frontend bootstrap-admin  ## Install all dependencies

.PHONY: bootstrap-backend
bootstrap-backend:  ## Install backend deps via uv
	cd backend && uv sync --all-extras

.PHONY: bootstrap-frontend
bootstrap-frontend:  ## Install frontend deps via bun
	cd frontend && bun install

.PHONY: bootstrap-admin
bootstrap-admin:  ## Install admin deps via bun
	cd admin && bun install

# ─── Dev servers (run from separate terminals) ────────────────────────────
.PHONY: dev
dev: up dev-backend  ## Start docker services + backend in foreground

.PHONY: dev-backend
dev-backend:  ## Run FastAPI in dev mode
	cd backend && uv run uvicorn dogeapi.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: dev-frontend
dev-frontend:  ## Run Next.js tenant app
	cd frontend && bun run dev

.PHONY: dev-admin
dev-admin:  ## Run Next.js admin portal
	cd admin && bun run dev

# ─── Docker compose ───────────────────────────────────────────────────────
.PHONY: up
up:  ## Start postgres + redis + mailpit
	docker compose -f infra/docker-compose.yml up -d postgres redis mailpit

.PHONY: down
down:  ## Stop and remove containers
	docker compose -f infra/docker-compose.yml down

.PHONY: nuke
nuke:  ## Stop and remove containers + volumes (destroys data)
	docker compose -f infra/docker-compose.yml down -v

.PHONY: logs
logs:  ## Tail compose logs
	docker compose -f infra/docker-compose.yml logs -f

# ─── Database ─────────────────────────────────────────────────────────────
.PHONY: migrate
migrate:  ## Apply pending Alembic migrations
	cd backend && uv run alembic upgrade head

.PHONY: migrate-down
migrate-down:  ## Rollback the latest Alembic migration
	cd backend && uv run alembic downgrade -1

.PHONY: revision
revision:  ## Create a new auto-generated migration: make revision m="add foo table"
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

.PHONY: psql
psql:  ## Open a psql shell
	docker compose -f infra/docker-compose.yml exec postgres psql -U dogeapi -d dogeapi

# ─── Test / lint ──────────────────────────────────────────────────────────
.PHONY: test
test: test-backend test-frontend test-admin  ## Run all test suites

.PHONY: test-backend
test-backend:  ## Run backend pytest
	cd backend && uv run pytest

.PHONY: test-backend-cov
test-backend-cov:  ## Run backend pytest with coverage
	cd backend && uv run pytest --cov=src/dogeapi --cov-report=term-missing

.PHONY: test-frontend
test-frontend:  ## Run frontend tests
	cd frontend && bun run test

.PHONY: test-admin
test-admin:  ## Run admin tests
	cd admin && bun run test

.PHONY: lint
lint: lint-backend lint-frontend lint-admin  ## Run all linters

.PHONY: lint-backend
lint-backend:  ## Lint + format-check backend
	cd backend && uv run ruff check . && uv run ruff format --check .

.PHONY: format-backend
format-backend:  ## Auto-format backend
	cd backend && uv run ruff check --fix . && uv run ruff format .

.PHONY: typecheck-backend
typecheck-backend:  ## Type-check backend
	cd backend && uv run mypy src

.PHONY: lint-frontend
lint-frontend:  ## Lint frontend
	cd frontend && bun run lint

.PHONY: lint-admin
lint-admin:  ## Lint admin
	cd admin && bun run lint

.PHONY: typecheck-frontend
typecheck-frontend:  ## Type-check frontend
	cd frontend && bun run typecheck

.PHONY: typecheck-admin
typecheck-admin:  ## Type-check admin
	cd admin && bun run typecheck

# ─── Cleanup ──────────────────────────────────────────────────────────────
.PHONY: clean
clean:  ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type d -name ".next" -prune -exec rm -rf {} +
	find . -type d -name "node_modules" -prune -exec rm -rf {} +
