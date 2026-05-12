"use client";

import Link from "next/link";
import { usePathname, useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { logout, me, type User } from "@/lib/auth";
import { switchOrg } from "@/lib/orgs";
import { OrgContextProvider, useOrgContext } from "@/lib/org-context";
import { Button } from "@/components/ui/button";
import {
  ErrorState,
  FeatureBadge,
  LoadingState,
} from "@/components/page-state";
import { frontendFeatures } from "@/lib/features";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/lib/api";

function OrgChrome({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { org, error, loading } = useOrgContext();
  const [user, setUser] = useState<User | null>(null);
  const [chromeError, setChromeError] = useState<string | null>(null);

  useEffect(() => {
    me()
      .then(setUser)
      .catch((err: ApiError) => {
        if (err.status === 401) router.replace("/login");
        else setChromeError(err.detail ?? "Failed to load profile");
      });
  }, [router]);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // ignore
    }
    router.replace("/login");
  }

  if (chromeError || error) {
    return (
      <ErrorState
        message={chromeError ?? error ?? "Failed to load organization"}
        actionHref="/dashboard"
        actionLabel="Back to organizations"
      />
    );
  }

  if (loading || !org || !user) {
    return <LoadingState label="Opening workspace" />;
  }

  const navItems = [
    { href: `/orgs/${slug}`, label: "Overview", enabled: true },
    { href: `/orgs/${slug}/members`, label: "Members", enabled: true },
    { href: `/orgs/${slug}/invitations`, label: "Invitations", enabled: true },
    {
      href: `/orgs/${slug}/api-keys`,
      label: "API keys",
      enabled: frontendFeatures.apiKeys,
    },
    {
      href: `/orgs/${slug}/audit-log`,
      label: "Audit log",
      enabled: frontendFeatures.auditLog,
    },
    {
      href: `/orgs/${slug}/billing`,
      label: "Billing",
      enabled: frontendFeatures.stripe,
    },
    {
      href: `/orgs/${slug}/ai`,
      label: "AI chat",
      enabled: frontendFeatures.aiChat,
    },
    {
      href: `/orgs/${slug}/ai/agents`,
      label: "AI agents",
      enabled: frontendFeatures.aiChat,
    },
    { href: `/orgs/${slug}/settings`, label: "Settings", enabled: true },
  ].filter((item) => item.enabled);

  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-full border border-border bg-background/70 px-3 py-1.5 text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground"
            >
              All organizations
            </Link>
            <span className="text-muted-foreground">/</span>
            <span className="text-lg font-semibold tracking-tight">
              {org.name}
            </span>
            <FeatureBadge tone="success">{org.role}</FeatureBadge>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-mono text-xs text-muted-foreground">
              {user.email}
            </span>
            <Button onClick={handleLogout} variant="ghost" size="sm">
              Sign out
            </Button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-6">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "whitespace-nowrap border-b-2 px-3 py-3 text-sm font-medium transition",
                  active
                    ? "border-primary font-medium text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
        {children}
      </div>
    </div>
  );
}

export default function OrgLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    switchOrg(slug)
      .then(() => setReady(true))
      .catch((err: ApiError) => {
        if (err.status === 401) router.replace("/login");
        else if (err.status === 403 || err.status === 404)
          router.replace("/dashboard");
        else setError(err.detail ?? "Failed to load organization");
      });
  }, [slug, router]);

  if (error) {
    return <ErrorState message={error} actionHref="/dashboard" />;
  }

  if (!ready) {
    return <LoadingState label="Switching organization" />;
  }

  return (
    <OrgContextProvider slug={slug}>
      <OrgChrome>{children}</OrgChrome>
    </OrgContextProvider>
  );
}
