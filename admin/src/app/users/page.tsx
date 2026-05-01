"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AdminShell } from "@/components/admin-shell";
import { listUsers, type AdminUser } from "@/lib/admin";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/lib/api";

export default function UsersPage() {
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    try {
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
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">Users</h1>
          <p className="text-sm text-muted-foreground">
            All registered accounts.
          </p>
        </header>

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

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Card>
          <CardContent className="p-0">
            {!users ? (
              <p className="px-6 py-4 text-sm text-muted-foreground">
                Loading…
              </p>
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
                        <span className="rounded-full bg-accent px-2 py-0.5 text-xs uppercase tracking-wider text-accent-foreground">
                          Super
                        </span>
                      )}
                      {!u.is_active && (
                        <span className="rounded-full border border-destructive px-2 py-0.5 text-xs uppercase tracking-wider text-destructive">
                          Inactive
                        </span>
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
