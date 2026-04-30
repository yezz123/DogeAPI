import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="space-y-4 text-center">
        <h1 className="text-5xl font-semibold tracking-tight">DogeAPI</h1>
        <p className="text-lg text-muted-foreground">
          Multi-tenant SaaS boilerplate &mdash; FastAPI &times; authx &times;
          Next.js
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/login"
          className="rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground transition hover:opacity-90"
        >
          Sign in
        </Link>
        <Link
          href="/register"
          className="rounded-md border border-border px-5 py-2.5 text-sm font-medium transition hover:bg-muted"
        >
          Create account
        </Link>
      </div>
    </main>
  );
}
