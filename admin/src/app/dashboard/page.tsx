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
import type { ApiError } from "@/lib/api";

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
        className="space-y-6"
      >
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">Overview</h1>
          <p className="text-sm text-muted-foreground">
            High-level health and recent tenants.
          </p>
        </header>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {health && (
          <div className="grid gap-3 sm:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Tenants</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-semibold">
                {health.total_orgs}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Users</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-semibold">
                {health.total_users}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">API keys</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-semibold">
                {health.total_api_keys}
              </CardContent>
            </Card>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent tenants</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {!tenants ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            ) : tenants.length === 0 ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                No tenants yet.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {tenants.map((t) => (
                  <li
                    key={t.id}
                    className="flex items-center justify-between px-6 py-3 text-sm"
                  >
                    <div>
                      <p className="font-medium">{t.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {t.slug} · {t.member_count} member
                        {t.member_count === 1 ? "" : "s"} · {t.plan}
                      </p>
                    </div>
                    <time className="text-xs text-muted-foreground">
                      {new Date(t.created_at).toLocaleDateString()}
                    </time>
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
