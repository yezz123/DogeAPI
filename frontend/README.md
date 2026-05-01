# AI Template Frontend

Next.js 16 (App Router, Turbopack default) tenant-facing SaaS UI. Tailwind v4,
Framer Motion, Zod. Managed with [bun](https://bun.com).

## Quick start

```bash
bun install
cp .env.example .env.local
bun run dev
```

App lives at `http://localhost:3000`. The backend is proxied at
`/api/backend/*` (configured in `next.config.ts`).

## Scripts

- `bun run dev` &mdash; dev server (Turbopack, default in Next.js 16)
- `bun run build` &mdash; production build
- `bun run start` &mdash; serve the production build
- `bun run lint` / `bun run lint:fix` &mdash; ESLint flat config
- `bun run typecheck` &mdash; TypeScript
- `bun run test` &mdash; Vitest

## Conventions

- Server-side data fetching via Server Components + Route Handlers
- Forms validated with Zod (shared schemas in `src/lib/validators.ts`)
- Auth lives in cookies (httpOnly + CSRF token, set by FastAPI/authx)
- Feature visibility gated by `NEXT_PUBLIC_FEATURE_*` env vars
