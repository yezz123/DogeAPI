-- Initial Postgres setup for DogeAPI.
-- Extensions are created at boot so Alembic migrations can rely on them.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
