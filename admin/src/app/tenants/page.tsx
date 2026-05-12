"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import { listTenants, type Tenant } from "@/lib/admin";
import { Card, CardContent } from "@/components/ui/card";
import {
  AdminPageHeader,
  EmptyPanel,
  InlineError,
  StatusPill,
  TableShell,
} from "@/components/admin-state";
import type { ApiError } from "@/lib/api";

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listTenants(200)
      .then(setTenants)
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
        <AdminPageHeader
          eyebrow="Organizations"
          title="Tenants"
          description="Every organization on the platform, including plan and member density."
        />

        {error && <InlineError message={error} />}

        <Card>
          <CardContent className="p-0">
            {!tenants ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            ) : tenants.length === 0 ? (
              <EmptyPanel
                title="No tenants yet"
                description="Once a user creates an organization in the tenant app, it will appear here."
              />
            ) : (
              <TableShell>
                <table className="w-full min-w-[720px] text-sm">
                  <thead className="border-b border-border text-xs uppercase tracking-[0.18em] text-muted-foreground">
                    <tr>
                      <th className="px-6 py-3 text-left">Name</th>
                      <th className="px-6 py-3 text-left">Slug</th>
                      <th className="px-6 py-3 text-left">Plan</th>
                      <th className="px-6 py-3 text-left">Members</th>
                      <th className="px-6 py-3 text-left">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {tenants.map((t) => (
                      <tr
                        key={t.id}
                        className="transition hover:bg-background/40"
                      >
                        <td className="px-6 py-4 font-medium">{t.name}</td>
                        <td className="px-6 py-4 font-mono text-xs text-muted-foreground">
                          {t.slug}
                        </td>
                        <td className="px-6 py-4">
                          <StatusPill tone="warning">{t.plan}</StatusPill>
                        </td>
                        <td className="px-6 py-4">{t.member_count}</td>
                        <td className="px-6 py-4 text-muted-foreground">
                          {new Date(t.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </TableShell>
            )}
          </CardContent>
        </Card>
      </motion.section>
    </AdminShell>
  );
}
