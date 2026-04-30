"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { requestPasswordReset } from "@/lib/password-reset";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [link, setLink] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const data = new FormData(event.currentTarget);
    try {
      const result = await requestPasswordReset(String(data.get("email")));
      setSubmitted(true);
      if (result.link) setLink(result.link);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.detail ?? "Failed to send reset link");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="w-full"
    >
      <Card>
        <CardHeader>
          <CardTitle>Forgot password</CardTitle>
          <CardDescription>
            Enter your email and we&apos;ll send a reset link.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {submitted ? (
            <div className="space-y-3 text-sm">
              <p>
                If an account exists for that email, a reset link has been sent.
              </p>
              {link && (
                <p className="text-xs text-muted-foreground">
                  Email delivery is disabled.{" "}
                  <a
                    href={link}
                    className="break-all text-primary hover:underline"
                  >
                    Open the reset link
                  </a>
                </p>
              )}
              <Link
                href="/login"
                className="inline-block text-sm font-medium text-primary hover:underline"
              >
                Back to sign in →
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Field>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                />
              </Field>
              {error && <FieldError>{error}</FieldError>}
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Sending…" : "Send reset link"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
      <p className="mt-4 text-center text-sm text-muted-foreground">
        Remember it?{" "}
        <Link
          href="/login"
          className="font-medium text-primary hover:underline"
        >
          Sign in
        </Link>
      </p>
    </motion.div>
  );
}
