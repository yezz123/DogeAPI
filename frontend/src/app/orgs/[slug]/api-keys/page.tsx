"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  createApiKey,
  listApiKeys,
  revokeApiKey,
  type APIKey,
} from "@/lib/api-keys";
import { useOrgContext } from "@/lib/org-context";
import { canManageApiKeys } from "@/lib/permissions";
import { scopesAvailableTo } from "@/lib/scope-helpers";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ApiError } from "@/lib/api";

export default function ApiKeysPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { role: myRole } = useOrgContext();
  const canManage = myRole ? canManageApiKeys(myRole) : false;
  const availableScopes = myRole ? scopesAvailableTo(myRole) : [];
  const [keys, setKeys] = useState<APIKey[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [revealedKey, setRevealedKey] = useState<string | null>(null);

  async function reload() {
    if (!slug || !canManage) return;
    try {
      setKeys(await listApiKeys(slug));
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Failed to load API keys");
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, canManage]);

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const form = event.currentTarget;
    const data = new FormData(form);
    const name = String(data.get("name") || "").trim();
    const scopes = data.getAll("scopes").map(String);

    if (!name) {
      setError("Name is required");
      return;
    }
    if (scopes.length === 0) {
      setError("Select at least one scope");
      return;
    }

    setSubmitting(true);
    try {
      const created = await createApiKey(slug, { name, scopes });
      setRevealedKey(created.plaintext_key);
      setShowForm(false);
      form.reset();
      reload();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Could not create key");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRevoke(key: APIKey) {
    if (!confirm(`Revoke "${key.name}"? Existing clients will stop working.`))
      return;
    try {
      await revokeApiKey(slug, key.id);
      reload();
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Could not revoke key");
    }
  }

  if (!canManage) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>API keys</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Your role doesn&apos;t allow managing API keys.
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
      <header className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">API keys</h1>
          <p className="text-sm text-muted-foreground">
            Per-organization keys with scoped permissions. Use the
            <code className="mx-1 rounded bg-muted px-1.5 py-0.5 text-xs">
              X-API-Key
            </code>
            header.
          </p>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)}>+ New API key</Button>
        )}
      </header>

      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Create API key</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreate} className="space-y-4">
                  <Field>
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      name="name"
                      placeholder="CI deployments"
                      maxLength={120}
                      required
                    />
                  </Field>
                  <Field>
                    <Label>Scopes</Label>
                    <div className="grid grid-cols-2 gap-2 rounded-md border border-border p-3">
                      {availableScopes.map((scope) => (
                        <label
                          key={scope}
                          className="flex items-center gap-2 text-sm"
                        >
                          <input
                            type="checkbox"
                            name="scopes"
                            value={scope}
                            className="h-4 w-4 rounded border-border"
                          />
                          <code className="text-xs">{scope}</code>
                        </label>
                      ))}
                    </div>
                  </Field>
                  {error && <FieldError>{error}</FieldError>}
                  <div className="flex gap-2">
                    <Button type="submit" disabled={submitting}>
                      {submitting ? "Creating…" : "Create key"}
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setShowForm(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* One-time reveal modal */}
      <AnimatePresence>
        {revealedKey && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 flex items-center justify-center bg-foreground/40 backdrop-blur-sm"
            onClick={() => setRevealedKey(null)}
          >
            <motion.div
              onClick={(e) => e.stopPropagation()}
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              className="z-50 w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl"
            >
              <h3 className="text-lg font-semibold">Copy your key now</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                This is the only time we&apos;ll show this key. Store it in a
                secrets manager.
              </p>
              <pre className="mt-4 break-all rounded-md bg-muted p-3 font-mono text-xs">
                {revealedKey}
              </pre>
              <div className="mt-4 flex justify-end gap-2">
                <Button
                  variant="secondary"
                  onClick={() => navigator.clipboard.writeText(revealedKey)}
                >
                  Copy
                </Button>
                <Button onClick={() => setRevealedKey(null)}>Done</Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <Card>
        <CardContent className="space-y-2 p-0">
          {keys === null ? (
            <p className="px-6 py-4 text-sm text-muted-foreground">Loading…</p>
          ) : keys.length === 0 ? (
            <p className="px-6 py-4 text-sm text-muted-foreground">
              No API keys yet.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {keys.map((k) => (
                <li
                  key={k.id}
                  className="flex items-center justify-between gap-4 px-6 py-4"
                >
                  <div className="space-y-1">
                    <p className="font-medium">{k.name}</p>
                    <p className="text-xs text-muted-foreground">
                      <code className="rounded bg-muted px-1 py-0.5 text-[11px]">
                        doge_{k.prefix}_…
                      </code>
                      {" · "}
                      {k.scopes.length} scope{k.scopes.length === 1 ? "" : "s"}
                      {" · created "}
                      {new Date(k.created_at).toLocaleDateString()}
                      {k.last_used_at && (
                        <>
                          {" · last used "}
                          {new Date(k.last_used_at).toLocaleDateString()}
                        </>
                      )}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleRevoke(k)}
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
