import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="space-y-4 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-primary">
          Operator console
        </p>
        <h1 className="text-5xl font-semibold tracking-tight">
          AI Template Admin
        </h1>
        <p className="mx-auto max-w-xl font-serif text-base leading-7 text-muted-foreground">
          Super-admin portal for the AI Template control plane, tuned for clear
          tenant, user, audit, and system-health operations.
        </p>
      </div>

      <Link
        href="/login"
        className="rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
      >
        Sign in
      </Link>
    </main>
  );
}
