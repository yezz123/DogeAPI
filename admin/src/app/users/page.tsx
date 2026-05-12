"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import { listUsers, type AdminUser } from "@/lib/admin";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  AdminPageHeader,
  EmptyPanel,
  InlineError,
  StatusPill,
} from "@/components/admin-state";
import type { ApiError } from "@/lib/api";

export default function UsersPage() {
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    try {
      setError(null);
      setUsers(null);
      setUsers(await listUsers({ email: filter || undefined }));
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
        <AdminPageHeader
          eyebrow="Identity"
          title="Users"
          description="Search accounts, check activation state, and confirm who can access the operator console."
        />

        <form
          onSubmit={(e) => {
            e.preventDefault();
            reload();
          }}
          className="flex gap-2"
        >
          <Input
            placeholder="Filter by email substring"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <Button type="submit">Search</Button>
        </form>

        {error && <InlineError message={error} />}

        <Card>
          <CardContent className="p-0">
            {!users ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
            ) : users.length === 0 ? (
              <EmptyPanel
                title="No matching users"
                description="Try a broader email filter or create an account from the tenant app."
              />
            ) : (
              <ul className="divide-y divide-border">
                {users.map((u) => (
                  <li
                    key={u.id}
                    className="flex items-center justify-between gap-4 px-6 py-3 text-sm"
                  >
                    <div>
                      <p className="font-medium">{u.full_name ?? u.email}</p>
                      <p className="text-xs text-muted-foreground">{u.email}</p>
                    </div>
                    <div className="flex gap-2">
                      {u.is_superadmin && (
                        <StatusPill tone="warning">Super</StatusPill>
                      )}
                      {!u.is_active && (
                        <StatusPill tone="danger">Inactive</StatusPill>
                      )}
                      {u.is_active && !u.is_superadmin && (
                        <StatusPill tone="success">Active</StatusPill>
                      )}
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
