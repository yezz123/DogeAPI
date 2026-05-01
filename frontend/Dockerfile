# syntax=docker/dockerfile:1.7
#
# Tenant frontend: Next.js 16 + bun build, node:20-alpine runtime.
# Uses Next.js's `output: "standalone"` so the runtime image only ships
# the minimal Node files needed to serve the app (~150MB).

ARG NODE_VERSION=20
ARG BUN_VERSION=1

# ─── Stage 1: dependencies ───────────────────────────────────────────────
FROM oven/bun:${BUN_VERSION}-alpine AS deps

WORKDIR /app

COPY package.json bun.lock ./
RUN --mount=type=cache,target=/root/.bun/install/cache \
    bun install --frozen-lockfile

# ─── Stage 2: builder ────────────────────────────────────────────────────
FROM oven/bun:${BUN_VERSION}-alpine AS builder

WORKDIR /app

# Public env vars must be present at build time so they get inlined into
# the bundle. Pass via --build-arg or compose `args:`.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_APP_NAME=DogeAPI
ARG NEXT_PUBLIC_FEATURE_OAUTH=false
ARG NEXT_PUBLIC_FEATURE_MAGIC_LINK=false
ARG NEXT_PUBLIC_FEATURE_AI_CHAT=false
ARG NEXT_PUBLIC_FEATURE_STRIPE=false
ARG NEXT_PUBLIC_FEATURE_API_KEYS=true
ARG NEXT_PUBLIC_FEATURE_AUDIT_LOG=true
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME \
    NEXT_PUBLIC_FEATURE_OAUTH=$NEXT_PUBLIC_FEATURE_OAUTH \
    NEXT_PUBLIC_FEATURE_MAGIC_LINK=$NEXT_PUBLIC_FEATURE_MAGIC_LINK \
    NEXT_PUBLIC_FEATURE_AI_CHAT=$NEXT_PUBLIC_FEATURE_AI_CHAT \
    NEXT_PUBLIC_FEATURE_STRIPE=$NEXT_PUBLIC_FEATURE_STRIPE \
    NEXT_PUBLIC_FEATURE_API_KEYS=$NEXT_PUBLIC_FEATURE_API_KEYS \
    NEXT_PUBLIC_FEATURE_AUDIT_LOG=$NEXT_PUBLIC_FEATURE_AUDIT_LOG \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN bun run build

# ─── Stage 3: runtime ────────────────────────────────────────────────────
FROM node:${NODE_VERSION}-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

# `output: "standalone"` produces a self-contained server bundle.
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
    CMD wget --quiet --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
