"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { logout, me, type User } from "@/lib/auth";
import { listOrgs, type OrgSummary } from "@/lib/orgs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ApiError } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [orgs, setOrgs] = useState<OrgSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([me(), listOrgs()])
      .then(([u, list]) => {
        setUser(u);
        setOrgs(list);
      })
      .catch((err: ApiError) => {
        if (err.status === 401) {
          router.replace("/login");
        } else {
          setError(err.detail ?? "Failed to load");
        }
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

  if (error) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-destructive">{error}</p>
      </main>
    );
  }

  if (!user || !orgs) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  return (
    <motion.main
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="mx-auto max-w-3xl space-y-8 px-6 py-12"
    >
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">
            Welcome, {user.full_name ?? user.email}
          </h1>
          <p className="text-sm text-muted-foreground">
            Pick an organization or create a new one.
          </p>
        </div>
        <Button onClick={handleLogout} variant="secondary">
          Sign out
        </Button>
      </header>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
            Your organizations
          </h2>
          <Link
            href="/orgs/new"
            className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:opacity-90"
          >
            + New organization
          </Link>
        </div>

        {orgs.length === 0 ? (
          <Card>
            <CardContent className="text-sm text-muted-foreground">
              You haven&apos;t joined any organizations yet. Create one to get
              started.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-3">
            {orgs.map((org) => (
              <Link key={org.id} href={`/orgs/${org.slug}`} className="block">
                <Card className="cursor-pointer transition hover:bg-muted">
                  <CardHeader className="flex flex-row items-start justify-between pb-0">
                    <div>
                      <CardTitle className="text-lg">{org.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">
                        {org.slug}
                      </p>
                    </div>
                    <span className="rounded-full border border-border px-2 py-0.5 text-xs uppercase tracking-wider text-muted-foreground">
                      {org.role}
                    </span>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </motion.main>
  );
}
