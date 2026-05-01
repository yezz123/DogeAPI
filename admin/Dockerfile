# syntax=docker/dockerfile:1.7
#
# Admin portal: Next.js 16 + bun build, node:20-alpine runtime.
# Same shape as ../frontend/Dockerfile but exposes port 3001.

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

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_APP_NAME="DogeAPI Admin"
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN bun run build

# ─── Stage 3: runtime ────────────────────────────────────────────────────
FROM node:${NODE_VERSION}-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3001 \
    HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3001

HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
    CMD wget --quiet --spider http://localhost:3001/ || exit 1

CMD ["node", "server.js"]
