"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import { getSystemHealth, type SystemHealth } from "@/lib/admin";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  AdminPageHeader,
  InlineError,
  StatusPill,
} from "@/components/admin-state";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/lib/api";

export default function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  async function reload() {
    try {
      setError(null);
      const next = await getSystemHealth();
      setHealth(next);
      setUpdatedAt(new Date());
    } catch (err) {
      setError((err as ApiError).detail ?? "Failed to load");
    }
  }

  useEffect(() => {
    reload();
  }, []);

  return (
    <AdminShell>
      <motion.section
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="space-y-6"
      >
        <AdminPageHeader
          eyebrow="Readiness"
          title="System health"
          description="Dependency state and platform totals from the backend admin health endpoint."
          actions={
            <Button type="button" variant="secondary" onClick={reload}>
              Refresh
            </Button>
          }
        />

        {error && <InlineError message={error} />}

        {updatedAt && (
          <p className="font-mono text-xs text-muted-foreground">
            Last updated {updatedAt.toLocaleTimeString()}
          </p>
        )}

        {health ? (
          <div className="grid gap-3 sm:grid-cols-2">
            <StatusCard label="Database" ok={health.db_ok} />
            <StatusCard label="Redis" ok={health.redis_ok} />
            <Counter label="Total tenants" value={health.total_orgs} />
            <Counter label="Total users" value={health.total_users} />
            <Counter label="Total API keys" value={health.total_api_keys} />
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {["Database", "Redis", "Total tenants", "Total users"].map(
              (label) => (
                <Card key={label}>
                  <CardHeader>
                    <CardTitle className="text-base">{label}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-8 w-20 animate-pulse rounded-full bg-background/60" />
                  </CardContent>
                </Card>
              ),
            )}
          </div>
        )}
      </motion.section>
    </AdminShell>
  );
}

function StatusCard({ label, ok }: { label: string; ok: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <StatusPill tone={ok ? "success" : "danger"}>
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              ok ? "bg-success" : "bg-destructive",
            )}
          />
          {ok ? "OK" : "Down"}
        </StatusPill>
      </CardContent>
    </Card>
  );
}

function Counter({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{label}</CardTitle>
      </CardHeader>
      <CardContent className="text-3xl font-semibold">{value}</CardContent>
    </Card>
  );
}
