# AI Template Admin Portal

Next.js 16 super-admin console for SaaS operators. Same stack as the tenant
frontend (Tailwind v4 + Framer Motion + Zod) on a separate port. Managed with
[bun](https://bun.com).

## Quick start

```bash
bun install
cp .env.example .env.local
bun run dev
```

App lives at `http://localhost:3001`. Only users marked
`is_superadmin = true` (and presenting an `admin:*` JWT scope) can sign in.

## Scripts

- `bun run dev` &mdash; dev server (Turbopack, default in Next.js 16)
- `bun run build` / `bun run start`
- `bun run lint` / `bun run lint:fix`
- `bun run typecheck`
- `bun run test`
