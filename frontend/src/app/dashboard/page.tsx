"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { logout, me, type User } from "@/lib/auth";
import { listOrgs, type OrgSummary } from "@/lib/orgs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  EmptyState,
  ErrorState,
  FeatureBadge,
  LoadingState,
  PageHeader,
} from "@/components/page-state";
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
      <ErrorState message={error} actionHref="/" actionLabel="Return home" />
    );
  }

  if (!user || !orgs) {
    return <LoadingState label="Loading organizations" />;
  }

  return (
    <motion.main
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="mx-auto max-w-5xl space-y-8 px-6 py-12"
    >
      <PageHeader
        eyebrow="Tenant console"
        title={`Welcome, ${user.full_name ?? user.email}`}
        description="Pick an organization, create a fresh workspace, or use this screen as the first-run hub for a new SaaS."
        actions={
          <>
            <Link
              href="/orgs/new"
              className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
            >
              New organization
            </Link>
            <Button onClick={handleLogout} variant="secondary">
              Sign out
            </Button>
          </>
        }
      />

      <section className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
          Your organizations
        </h2>

        {orgs.length === 0 ? (
          <EmptyState
            title="No workspaces yet"
            description="Create the first organization to try role-scoped auth, API keys, invitations, and audit-ready flows."
            action={
              <Link
                href="/orgs/new"
                className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90"
              >
                Create organization
              </Link>
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {orgs.map((org) => (
              <Link key={org.id} href={`/orgs/${org.slug}`} className="block">
                <Card className="group cursor-pointer transition hover:border-primary/50 hover:bg-muted/65">
                  <CardHeader className="flex flex-row items-start justify-between pb-0">
                    <div>
                      <CardTitle className="text-xl">{org.name}</CardTitle>
                      <p className="mt-1 font-mono text-xs text-muted-foreground">
                        {org.slug}
                      </p>
                    </div>
                    <FeatureBadge>{org.role}</FeatureBadge>
                  </CardHeader>
                  <CardContent className="pt-4 text-sm text-muted-foreground">
                    <p>
                      Open workspace <span className="ml-1">-&gt;</span>
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </motion.main>
  );
}
