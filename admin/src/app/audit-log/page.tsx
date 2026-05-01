"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import { listAuditLog, type AuditEntry } from "@/lib/admin";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/lib/api";

export default function AdminAuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const [orgFilter, setOrgFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    try {
      setEntries(
        await listAuditLog({
          org_id: orgFilter || undefined,
          action: actionFilter || undefined,
        }),
      );
    } catch (err) {
      setError((err as ApiError).detail ?? "Failed to load");
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
            Cross-tenant audit log
          </h1>
          <p className="text-sm text-muted-foreground">
            Mutations recorded across every organization.
          </p>
        </header>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            reload();
          }}
          className="grid grid-cols-1 gap-2 sm:grid-cols-3"
        >
          <Input
            placeholder="Org id (UUID)"
            value={orgFilter}
            onChange={(e) => setOrgFilter(e.target.value)}
          />
          <Input
            placeholder="Action (e.g. invitation.created)"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          />
          <Button type="submit">Filter</Button>
        </form>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Card>
          <CardContent className="p-0">
            {!entries ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            ) : entries.length === 0 ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                No matching entries.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {entries.map((entry) => (
                  <li key={entry.id} className="px-6 py-3 text-sm">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-medium">{entry.action}</p>
                        <p className="font-mono text-xs text-muted-foreground">
                          {entry.method} {entry.path} → {entry.status_code}
                        </p>
                        {entry.org_id && (
                          <p className="text-xs text-muted-foreground">
                            org: {entry.org_id}
                          </p>
                        )}
                      </div>
                      <time className="text-xs text-muted-foreground">
                        {new Date(entry.created_at).toLocaleString()}
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
