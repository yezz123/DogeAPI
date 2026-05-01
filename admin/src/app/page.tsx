import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-8 px-6 py-16">
      <div className="space-y-3 text-center">
        <p className="text-xs uppercase tracking-widest text-accent">
          Operator console
        </p>
        <h1 className="text-5xl font-semibold tracking-tight">
          AI Template Admin
        </h1>
        <p className="text-base text-muted-foreground">
          Super-admin portal for the AI Template control plane.
        </p>
      </div>

      <Link
        href="/login"
        className="rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition hover:opacity-90"
      >
        Sign in
      </Link>
    </main>
  );
}
