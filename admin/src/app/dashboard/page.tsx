"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import {
  getSystemHealth,
  listTenants,
  type SystemHealth,
  type Tenant,
} from "@/lib/admin";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AdminPageHeader,
  EmptyPanel,
  InlineError,
  StatusPill,
} from "@/components/admin-state";
import type { ApiError } from "@/lib/api";

const STAT_COPY = {
  tenants: {
    label: "Tenants",
    detail: "Organizations under management",
  },
  users: {
    label: "Users",
    detail: "Registered identities",
  },
  apiKeys: {
    label: "API keys",
    detail: "Issued machine credentials",
  },
};

export default function AdminDashboardPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [tenants, setTenants] = useState<Tenant[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getSystemHealth(), listTenants(5)])
      .then(([h, t]) => {
        setHealth(h);
        setTenants(t);
      })
      .catch((err: ApiError) => setError(err.detail ?? "Failed to load"));
  }, []);

  return (
    <AdminShell>
      <motion.section
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="space-y-5"
      >
        <section className="relative overflow-hidden rounded-[1.75rem] border border-border bg-background">
          <div className="absolute inset-x-8 top-8 grid grid-cols-12 gap-2 opacity-50">
            {Array.from({ length: 96 }).map((_, index) => (
              <span
                key={index}
                className="h-1.5 rounded-full bg-muted"
                style={{
                  opacity:
                    index % 9 === 0 ? 0.95 : index % 5 === 0 ? 0.55 : 0.22,
                }}
              />
            ))}
          </div>
          <div className="relative grid gap-8 p-6 lg:grid-cols-[1fr_18rem] lg:p-8">
            <AdminPageHeader
              eyebrow="Control plane"
              title="Operator overview"
              description="A quieter command surface for watching tenants, users, API keys, and the health of the platform."
            />
            <div className="rounded-[1.25rem] border border-border bg-muted/60 p-5 shadow-sm">
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.28em] text-primary">
                Current posture
              </p>
              <div className="mt-5 space-y-3">
                <HealthLine label="Database" ok={health?.db_ok} />
                <HealthLine label="Redis" ok={health?.redis_ok} />
              </div>
            </div>
          </div>
        </section>

        {error && <InlineError message={error} />}

        {health ? (
          <div className="grid gap-4 lg:grid-cols-3">
            <MetricCard
              label={STAT_COPY.tenants.label}
              detail={STAT_COPY.tenants.detail}
              value={health.total_orgs}
              tone="primary"
            />
            <MetricCard
              label={STAT_COPY.users.label}
              detail={STAT_COPY.users.detail}
              value={health.total_users}
              tone="accent"
            />
            <MetricCard
              label={STAT_COPY.apiKeys.label}
              detail={STAT_COPY.apiKeys.detail}
              value={health.total_api_keys}
              tone="success"
            />
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-3">
            {["Tenants", "Users", "API keys"].map((label) => (
              <Card key={label}>
                <CardHeader>
                  <CardTitle className="text-sm">{label}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-9 w-16 animate-pulse rounded-full bg-background/60" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Card className="overflow-hidden p-0 shadow-sm">
          <CardHeader className="border-b border-border bg-background px-6 py-5">
            <div>
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-primary">
                Tenant activity
              </p>
              <CardTitle className="mt-2 text-xl">Recent tenants</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {!tenants ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            ) : tenants.length === 0 ? (
              <EmptyPanel
                title="No tenants yet"
                description="Create a workspace from the tenant app to see it appear here."
              />
            ) : (
              <ul className="divide-y divide-border">
                {tenants.map((t) => (
                  <li
                    key={t.id}
                    className="grid gap-4 px-6 py-4 text-sm transition hover:bg-muted/55 sm:grid-cols-[1fr_auto]"
                  >
                    <div>
                      <p className="text-base font-semibold tracking-tight">
                        {t.name}
                      </p>
                      <p className="mt-1 font-mono text-xs text-muted-foreground">
                        {t.slug} · {t.member_count} member
                        {t.member_count === 1 ? "" : "s"}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 sm:justify-end">
                      <StatusPill tone="warning">{t.plan}</StatusPill>
                      <time className="text-xs text-muted-foreground">
                        {new Date(t.created_at).toLocaleDateString()}
                      </time>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </motion.section>
    </AdminShell>
  );
}

function MetricCard({
  label,
  detail,
  value,
  tone,
}: {
  label: string;
  detail: string;
  value: number;
  tone: "primary" | "accent" | "success";
}) {
  const toneClass =
    tone === "primary"
      ? "bg-primary"
      : tone === "accent"
        ? "bg-accent"
        : "bg-success";

  return (
    <Card className="relative overflow-hidden p-0 shadow-sm">
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold">{label}</p>
            <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
          </div>
          <span className={`h-2.5 w-2.5 rounded-full ${toneClass}`} />
        </div>
        <p className="mt-8 text-5xl font-semibold tracking-[-0.06em]">
          {value}
        </p>
      </div>
      <div className={`h-1.5 w-full ${toneClass}`} />
    </Card>
  );
}

function HealthLine({ label, ok }: { label: string; ok?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="inline-flex items-center gap-2 font-medium">
        <span
          className={
            ok === undefined
              ? "h-2 w-2 rounded-full bg-muted-foreground/40"
              : ok
                ? "h-2 w-2 rounded-full bg-success"
                : "h-2 w-2 rounded-full bg-destructive"
          }
        />
        {ok === undefined ? "Checking" : ok ? "Online" : "Down"}
      </span>
    </div>
  );
}
