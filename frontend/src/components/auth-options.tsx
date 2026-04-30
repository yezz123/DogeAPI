"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { requestMagicLink } from "@/lib/magic-link";
import { Button } from "@/components/ui/button";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { readPublicFlag } from "@/lib/utils";
import type { ApiError } from "@/lib/api";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function AuthOptions() {
  const oauthEnabled = readPublicFlag("FEATURE_OAUTH");
  const magicLinkEnabled = readPublicFlag("FEATURE_MAGIC_LINK");
  const [magicLinkOpen, setMagicLinkOpen] = useState(false);
  const [magicEmail, setMagicEmail] = useState("");
  const [magicResult, setMagicResult] = useState<string | null>(null);
  const [magicLink, setMagicLink] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!oauthEnabled && !magicLinkEnabled) return null;

  async function handleMagicSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMagicLink(null);
    setSubmitting(true);
    try {
      const result = await requestMagicLink(magicEmail);
      setMagicResult("Check your inbox for a sign-in link.");
      if (result.link) setMagicLink(result.link);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Could not send magic link");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mt-6 space-y-4">
      <div className="relative flex items-center">
        <div className="flex-grow border-t border-border" />
        <span className="mx-3 text-xs uppercase tracking-wider text-muted-foreground">
          or
        </span>
        <div className="flex-grow border-t border-border" />
      </div>

      {oauthEnabled && (
        <div className="space-y-2">
          <a
            href={`${apiBase}/auth/oauth/google/start`}
            className="flex w-full items-center justify-center rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            Continue with Google
          </a>
          <a
            href={`${apiBase}/auth/oauth/github/start`}
            className="flex w-full items-center justify-center rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-muted"
          >
            Continue with GitHub
          </a>
        </div>
      )}

      {magicLinkEnabled && (
        <div>
          <Button
            type="button"
            variant="ghost"
            className="w-full"
            onClick={() => setMagicLinkOpen((v) => !v)}
          >
            {magicLinkOpen ? "Hide" : "Sign in with magic link"}
          </Button>
          <AnimatePresence>
            {magicLinkOpen && (
              <motion.form
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                onSubmit={handleMagicSubmit}
                className="mt-3 space-y-3"
              >
                <Field>
                  <Label htmlFor="magic-email">Email</Label>
                  <Input
                    id="magic-email"
                    type="email"
                    value={magicEmail}
                    onChange={(e) => setMagicEmail(e.target.value)}
                    required
                  />
                </Field>
                {error && <FieldError>{error}</FieldError>}
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Sending…" : "Send link"}
                </Button>
                {magicResult && (
                  <p className="text-xs text-muted-foreground">{magicResult}</p>
                )}
                {magicLink && (
                  <p className="text-xs text-muted-foreground">
                    Email delivery is disabled.{" "}
                    <a
                      href={magicLink}
                      className="break-all text-primary hover:underline"
                    >
                      Use this link
                    </a>
                  </p>
                )}
              </motion.form>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
