"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import { listTenants, type Tenant } from "@/lib/admin";
import { Card, CardContent } from "@/components/ui/card";
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
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">Tenants</h1>
          <p className="text-sm text-muted-foreground">
            Every organization on the platform.
          </p>
        </header>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Card>
          <CardContent className="p-0">
            {!tenants ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-6 py-2 text-left">Name</th>
                    <th className="px-6 py-2 text-left">Slug</th>
                    <th className="px-6 py-2 text-left">Plan</th>
                    <th className="px-6 py-2 text-left">Members</th>
                    <th className="px-6 py-2 text-left">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {tenants.map((t) => (
                    <tr key={t.id}>
                      <td className="px-6 py-3 font-medium">{t.name}</td>
                      <td className="px-6 py-3 text-muted-foreground">
                        {t.slug}
                      </td>
                      <td className="px-6 py-3">
                        <span className="rounded-full border border-border px-2 py-0.5 text-xs uppercase tracking-wider text-muted-foreground">
                          {t.plan}
                        </span>
                      </td>
                      <td className="px-6 py-3">{t.member_count}</td>
                      <td className="px-6 py-3 text-muted-foreground">
                        {new Date(t.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </motion.section>
    </AdminShell>
  );
}
