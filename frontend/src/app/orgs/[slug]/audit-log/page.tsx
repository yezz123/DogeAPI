"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { listAuditLog, type AuditLogEntry } from "@/lib/audit-log";
import { useOrgContext } from "@/lib/org-context";
import { canViewAuditLog } from "@/lib/permissions";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/lib/api";

export default function AuditLogPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { role: myRole } = useOrgContext();
  const canView = myRole ? canViewAuditLog(myRole) : false;
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState("");

  async function reload() {
    if (!slug || !canView) return;
    try {
      setEntries(
        await listAuditLog(slug, {
          action: actionFilter || undefined,
          limit: 100,
        }),
      );
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Failed to load audit log");
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, canView]);

  if (!canView) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Audit log</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Your role doesn&apos;t allow viewing the audit log.
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6"
    >
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Audit log</h1>
        <p className="text-sm text-muted-foreground">
          Every successful mutation is recorded with actor, action, and
          metadata.
        </p>
      </header>

      <Card>
        <CardContent className="p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              reload();
            }}
            className="flex gap-2"
          >
            <Input
              placeholder="Filter by action (e.g. invitation.created)"
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            />
            <Button type="submit">Filter</Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setActionFilter("");
                reload();
              }}
            >
              Clear
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Card>
        <CardContent className="space-y-2 p-0">
          {entries === null ? (
            <p className="px-6 py-4 text-sm text-muted-foreground">Loading…</p>
          ) : entries.length === 0 ? (
            <p className="px-6 py-4 text-sm text-muted-foreground">
              No audit log entries.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {entries.map((entry) => (
                <li key={entry.id} className="px-6 py-3">
                  <div className="flex items-start justify-between gap-4 text-sm">
                    <div className="space-y-0.5">
                      <p className="font-medium">{entry.action}</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {entry.method} {entry.path} → {entry.status_code}
                      </p>
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
  );
}
