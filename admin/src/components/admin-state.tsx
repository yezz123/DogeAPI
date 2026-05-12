import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function AdminPageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div className="max-w-2xl space-y-2">
        {eyebrow && (
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-primary">
            {eyebrow}
          </p>
        )}
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          {title}
        </h1>
        {description && (
          <p className="font-serif text-sm leading-6 text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </header>
  );
}

export function AdminLoading({
  label = "Loading operator data",
}: {
  label?: string;
}) {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl items-center px-6 py-16">
      <div className="w-full space-y-5">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-primary">
          {label}
        </p>
        <div className="space-y-3">
          <div className="h-4 w-2/3 animate-pulse rounded-full bg-muted" />
          <div className="h-4 w-1/2 animate-pulse rounded-full bg-muted" />
          <div className="h-28 animate-pulse rounded-(--radius) border border-border bg-muted/70" />
        </div>
      </div>
    </main>
  );
}

export function AdminError({
  message,
  title = "Operator console needs attention",
  href = "/login",
}: {
  message: string;
  title?: string;
  href?: string;
}) {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl items-center px-6 py-16">
      <div className="rounded-(--radius) border border-destructive/40 bg-muted/80 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-destructive">
          Error
        </p>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-2 font-serif text-sm leading-6 text-muted-foreground">
          {message}
        </p>
        <Link
          href={href}
          className="mt-5 inline-flex rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
        >
          Continue
        </Link>
      </div>
    </main>
  );
}

export function InlineError({ message }: { message: string }) {
  return (
    <div className="rounded-(--radius) border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
      {message}
    </div>
  );
}

export function EmptyPanel({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="px-6 py-8 text-center">
      <p className="font-semibold tracking-tight">{title}</p>
      <p className="mx-auto mt-2 max-w-sm font-serif text-sm leading-6 text-muted-foreground">
        {description}
      </p>
    </div>
  );
}

export function TableShell({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("overflow-x-auto rounded-(--radius)", className)}>
      {children}
    </div>
  );
}

export function StatusPill({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.18em]",
        tone === "success" &&
          "border-success/40 bg-success/15 text-muted-foreground",
        tone === "warning" &&
          "border-primary/40 bg-primary/15 text-muted-foreground",
        tone === "danger" &&
          "border-destructive/40 bg-destructive/15 text-destructive",
        tone === "neutral" &&
          "border-border bg-background/55 text-muted-foreground",
      )}
    >
      {children}
    </span>
  );
}
