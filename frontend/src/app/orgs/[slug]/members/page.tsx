"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  changeMemberRole,
  listMembers,
  removeMember,
  type Member,
  type Role,
} from "@/lib/orgs";
import { useOrgContext } from "@/lib/org-context";
import { canManageMembers } from "@/lib/permissions";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/lib/api";

const ROLES: Role[] = ["owner", "admin", "member"];

export default function MembersPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { role: myRole } = useOrgContext();
  const [members, setMembers] = useState<Member[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const canManage = myRole ? canManageMembers(myRole) : false;

  async function reload() {
    if (!slug) return;
    try {
      setMembers(await listMembers(slug));
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Failed to load members");
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  async function handleRoleChange(member: Member, role: Role) {
    try {
      await changeMemberRole(slug, member.user_id, role);
      reload();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Could not update role");
    }
  }

  async function handleRemove(member: Member) {
    if (!confirm(`Remove ${member.email} from the organization?`)) return;
    try {
      await removeMember(slug, member.user_id);
      reload();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Could not remove member");
    }
  }

  if (!members) {
    return <p className="text-sm text-muted-foreground">Loading members…</p>;
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6"
    >
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Members</h1>
        <p className="text-sm text-muted-foreground">
          People with access to this organization.
        </p>
      </header>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Card>
        <CardContent className="divide-y divide-border p-0">
          {members.map((m) => (
            <div
              key={m.user_id}
              className="flex items-center justify-between gap-4 px-6 py-4"
            >
              <div>
                <p className="font-medium">{m.full_name ?? m.email}</p>
                <p className="text-xs text-muted-foreground">{m.email}</p>
              </div>
              <div className="flex items-center gap-2">
                {canManage ? (
                  <select
                    value={m.role}
                    onChange={(e) =>
                      handleRoleChange(m, e.target.value as Role)
                    }
                    className="h-9 rounded-md border border-border bg-background px-2 text-sm"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="rounded-full border border-border px-2 py-0.5 text-xs uppercase tracking-wider text-muted-foreground">
                    {m.role}
                  </span>
                )}
                {canManage && (
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleRemove(m)}
                  >
                    Remove
                  </Button>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </motion.section>
  );
}
