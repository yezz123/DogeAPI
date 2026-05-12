import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-5 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between",
        className,
      )}
    >
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
          <p className="font-serif text-base leading-7 text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </header>
  );
}

export function LoadingState({
  label = "Loading workspace",
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
          <div className="h-24 animate-pulse rounded-[var(--radius)] border border-border bg-muted/70" />
        </div>
      </div>
    </main>
  );
}

export function ErrorState({
  title = "Something needs attention",
  message,
  actionHref,
  actionLabel = "Go back",
}: {
  title?: string;
  message: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl items-center px-6 py-16">
      <div className="rounded-[var(--radius)] border border-destructive/40 bg-background/85 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-destructive">
          Error
        </p>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-2 font-serif text-sm leading-6 text-muted-foreground">
          {message}
        </p>
        {actionHref && (
          <Link
            href={actionHref}
            className="mt-5 inline-flex rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
          >
            {actionLabel}
          </Link>
        )}
      </div>
    </main>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-[var(--radius)] border border-dashed border-border bg-muted/35 p-8 text-center">
      <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      <p className="mx-auto mt-2 max-w-md font-serif text-sm leading-6 text-muted-foreground">
        {description}
      </p>
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}

export function FeatureBadge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "accent" | "success";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.18em]",
        tone === "accent" &&
          "border-accent/40 bg-accent/15 text-muted-foreground",
        tone === "success" &&
          "border-success/40 bg-success/15 text-muted-foreground",
        tone === "neutral" &&
          "border-border bg-background/65 text-muted-foreground",
      )}
    >
      {children}
    </span>
  );
}
