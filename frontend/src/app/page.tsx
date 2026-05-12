import Link from "next/link";

const STACK = ["FastAPI", "authx", "SQLAlchemy", "Next.js 16", "Tailwind v4"];

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-hidden px-6 py-6">
      <section className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-7xl grid-cols-1 gap-8 rounded-[2rem] border border-border bg-background/80 p-6 backdrop-blur-md lg:grid-cols-[1.05fr_0.95fr] lg:p-10">
        <div className="flex flex-col justify-between gap-12">
          <header className="flex items-center justify-between">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              AI Template
            </Link>
            <nav className="flex items-center gap-2 text-sm">
              <Link
                href="/login"
                className="rounded-full px-4 py-2 text-muted-foreground transition hover:bg-muted hover:text-foreground"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-full bg-primary px-4 py-2 font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                Create account
              </Link>
            </nav>
          </header>

          <div className="max-w-3xl space-y-8">
            <div className="inline-flex rounded-full border border-border bg-muted/50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-primary">
              Backend-first SaaS boilerplate
            </div>
            <div className="space-y-5">
              <h1 className="max-w-4xl text-5xl font-semibold leading-[0.95] tracking-tight sm:text-7xl">
                A calmer way to start a serious SaaS.
              </h1>
              <p className="max-w-2xl font-serif text-lg leading-8 text-muted-foreground">
                AI Template pairs a stable FastAPI control plane with polished
                tenant and admin apps, so new projects start with auth,
                organizations, API keys, audit trails, and operator workflows
                already in place.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/register"
                className="rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                Start a workspace
              </Link>
              <a
                href="http://localhost:8000/docs"
                className="rounded-full border border-border bg-background/70 px-6 py-3 text-sm font-semibold transition hover:bg-muted"
              >
                Open API docs
              </a>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            {STACK.map((item) => (
              <div
                key={item}
                className="rounded-2xl border border-border bg-muted/45 px-4 py-3 text-sm font-semibold"
              >
                {item}
              </div>
            ))}
          </div>
        </div>

        <aside className="relative flex min-h-[32rem] flex-col justify-end overflow-hidden rounded-[1.5rem] border border-border bg-foreground p-6 text-background">
          <div className="absolute inset-x-8 top-8 grid grid-cols-6 gap-2 opacity-80">
            {Array.from({ length: 84 }).map((_, index) => (
              <span
                key={index}
                className="h-2 rounded-full bg-background/20"
                style={{
                  opacity:
                    index % 7 === 0 ? 0.9 : index % 5 === 0 ? 0.55 : 0.24,
                }}
              />
            ))}
          </div>
          <div className="relative space-y-6">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-primary">
              First run path
            </p>
            <div className="space-y-3 font-mono text-sm">
              <p>cp .env.example .env</p>
              <p>make bootstrap</p>
              <p>make stack-up</p>
              <p>open :3000 / :3001 / :8000/docs</p>
            </div>
            <div className="grid gap-3 border-t border-background/20 pt-6 sm:grid-cols-2">
              <Metric value="3" label="apps wired together" />
              <Metric value="9+" label="feature modules" />
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <p className="text-3xl font-semibold tracking-tight">{value}</p>
      <p className="mt-1 text-xs uppercase tracking-[0.22em] text-background/60">
        {label}
      </p>
    </div>
  );
}
