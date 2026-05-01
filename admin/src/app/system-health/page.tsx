"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import { getSystemHealth, type SystemHealth } from "@/lib/admin";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/lib/api";

export default function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSystemHealth()
      .then(setHealth)
      .catch((err: ApiError) => setError(err.detail ?? "Failed to load"));
  }, []);

  return (
    <AdminShell>
      <motion.section
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="space-y-6"
      >
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">
            System health
          </h1>
        </header>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {health && (
          <div className="grid gap-3 sm:grid-cols-2">
            <StatusCard label="Database" ok={health.db_ok} />
            <StatusCard label="Redis" ok={health.redis_ok} />
            <Counter label="Total tenants" value={health.total_orgs} />
            <Counter label="Total users" value={health.total_users} />
            <Counter label="Total API keys" value={health.total_api_keys} />
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
        <span
          className={cn(
            "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider",
            ok
              ? "bg-accent/30 text-accent-foreground"
              : "bg-destructive/40 text-destructive-foreground",
          )}
        >
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              ok ? "bg-accent" : "bg-destructive",
            )}
          />
          {ok ? "OK" : "Down"}
        </span>
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
