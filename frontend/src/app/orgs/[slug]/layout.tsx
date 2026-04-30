"use client";

import Link from "next/link";
import { usePathname, useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { logout, me, type User } from "@/lib/auth";
import { switchOrg } from "@/lib/orgs";
import { OrgContextProvider, useOrgContext } from "@/lib/org-context";
import { Button } from "@/components/ui/button";
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
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-destructive">{chromeError ?? error}</p>
      </main>
    );
  }

  if (loading || !org || !user) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  const navItems = [
    { href: `/orgs/${slug}`, label: "Overview" },
    { href: `/orgs/${slug}/members`, label: "Members" },
    { href: `/orgs/${slug}/invitations`, label: "Invitations" },
    { href: `/orgs/${slug}/api-keys`, label: "API keys" },
    { href: `/orgs/${slug}/audit-log`, label: "Audit log" },
    { href: `/orgs/${slug}/billing`, label: "Billing" },
    { href: `/orgs/${slug}/ai`, label: "AI chat" },
    { href: `/orgs/${slug}/settings`, label: "Settings" },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="text-sm text-muted-foreground hover:underline"
            >
              ← All organizations
            </Link>
            <span className="text-muted-foreground">/</span>
            <span className="font-semibold">{org.name}</span>
            <span className="rounded-full border border-border px-2 py-0.5 text-xs uppercase tracking-wider text-muted-foreground">
              {org.role}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">{user.email}</span>
            <Button onClick={handleLogout} variant="ghost" size="sm">
              Sign out
            </Button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 px-6">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "border-b-2 px-3 py-2 text-sm transition",
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
      <div className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
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
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-destructive">{error}</p>
      </main>
    );
  }

  if (!ready) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  return (
    <OrgContextProvider slug={slug}>
      <OrgChrome>{children}</OrgChrome>
    </OrgContextProvider>
  );
}
