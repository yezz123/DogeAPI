"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  createInvitation,
  listInvitations,
  revokeInvitation,
  type Invitation,
  type Role,
} from "@/lib/orgs";
import { useOrgContext } from "@/lib/org-context";
import { canManageInvitations } from "@/lib/permissions";
import { inviteSchema } from "@/lib/validators";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ApiError } from "@/lib/api";

const ROLES: Role[] = ["owner", "admin", "member"];

export default function InvitationsPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { role: myRole } = useOrgContext();
  const canManage = myRole ? canManageInvitations(myRole) : false;
  const [invitations, setInvitations] = useState<Invitation[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function reload() {
    if (!slug || !canManage) return;
    try {
      setInvitations(await listInvitations(slug));
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Failed to load invitations");
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, canManage]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLink(null);
    const form = event.currentTarget;
    const data = new FormData(form);
    const parsed = inviteSchema.safeParse({
      email: data.get("email"),
      role: data.get("role"),
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Invalid input");
      return;
    }

    setSubmitting(true);
    try {
      const created = await createInvitation(slug, parsed.data);
      if (created.invite_link) setLink(created.invite_link);
      reload();
      form.reset();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Could not send invite");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRevoke(id: string) {
    try {
      await revokeInvitation(slug, id);
      reload();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Could not revoke invitation");
    }
  }

  if (!canManage) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invitations</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Your role doesn&apos;t allow managing invitations.
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
        <h1 className="text-2xl font-semibold tracking-tight">Invitations</h1>
        <p className="text-sm text-muted-foreground">
          Invite teammates to join this organization.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">New invitation</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit}
            className="grid grid-cols-[1fr,140px,auto] gap-3"
          >
            <Field>
              <Label htmlFor="email" className="sr-only">
                Email
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="teammate@example.com"
                required
              />
            </Field>
            <Field>
              <Label htmlFor="role" className="sr-only">
                Role
              </Label>
              <select
                id="role"
                name="role"
                defaultValue="member"
                className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm"
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </Field>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Sending…" : "Send invite"}
            </Button>
          </form>
          {error && <FieldError className="mt-2">{error}</FieldError>}
          {link && (
            <p className="mt-3 text-xs text-muted-foreground">
              Email delivery is disabled. Share this link directly:
              <a
                href={link}
                className="ml-2 break-all text-primary hover:underline"
              >
                {link}
              </a>
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Pending invitations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 p-0">
          {!invitations ? (
            <p className="px-6 py-4 text-sm text-muted-foreground">Loading…</p>
          ) : invitations.length === 0 ? (
            <p className="px-6 py-4 text-sm text-muted-foreground">
              No pending invitations.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {invitations.map((inv) => (
                <li
                  key={inv.id}
                  className="flex items-center justify-between gap-4 px-6 py-3"
                >
                  <div>
                    <p className="font-medium">{inv.email}</p>
                    <p className="text-xs text-muted-foreground">
                      {inv.role} · expires{" "}
                      {new Date(inv.expires_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleRevoke(inv.id)}
                  >
                    Revoke
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </motion.section>
  );
}
