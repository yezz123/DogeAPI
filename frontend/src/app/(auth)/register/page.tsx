"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { motion } from "framer-motion";
import { register } from "@/lib/auth";
import { registerSchema } from "@/lib/validators";
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

type FieldErrors = Partial<
  Record<"email" | "password" | "full_name" | "form", string>
>;

export default function RegisterPage() {
  const router = useRouter();
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [verifyLink, setVerifyLink] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors({});
    const data = new FormData(event.currentTarget);
    const parsed = registerSchema.safeParse({
      email: data.get("email"),
      password: data.get("password"),
      full_name: data.get("full_name") || undefined,
    });
    if (!parsed.success) {
      const fieldErrors: FieldErrors = {};
      for (const issue of parsed.error.issues) {
        fieldErrors[issue.path[0] as keyof FieldErrors] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    setSubmitting(true);
    try {
      const response = await register(parsed.data);
      if (response.email_verification_link) {
        setVerifyLink(response.email_verification_link);
      } else {
        router.push("/dashboard");
        router.refresh();
      }
    } catch (err) {
      const apiErr = err as ApiError;
      setErrors({ form: apiErr.detail ?? "Could not create your account" });
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
          <CardTitle>Create your account</CardTitle>
          <CardDescription>
            Spin up a new AI Template workspace in seconds.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {verifyLink ? (
            <div className="space-y-3">
              <p className="text-sm">
                Account created! Email delivery is disabled in this environment,
                so use the verification link below to confirm your address.
              </p>
              <a
                href={verifyLink}
                className="block break-all rounded-md border border-border bg-muted p-3 text-xs text-primary hover:underline"
              >
                {verifyLink}
              </a>
              <Button
                onClick={() => router.push("/dashboard")}
                className="w-full"
              >
                Continue to dashboard
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Field>
                <Label htmlFor="full_name">Name (optional)</Label>
                <Input
                  id="full_name"
                  name="full_name"
                  autoComplete="name"
                  placeholder="Alice Liddell"
                />
                <FieldError>{errors.full_name}</FieldError>
              </Field>
              <Field>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                />
                <FieldError>{errors.email}</FieldError>
              </Field>
              <Field>
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
                <FieldError>{errors.password}</FieldError>
              </Field>
              <FieldError>{errors.form}</FieldError>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Creating account…" : "Create account"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
      <p className="mt-4 text-center text-sm text-muted-foreground">
        Already have one?{" "}
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
