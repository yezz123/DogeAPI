"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { motion } from "framer-motion";
import { createOrg, switchOrg } from "@/lib/orgs";
import { createOrgSchema } from "@/lib/validators";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, FieldError } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ApiError } from "@/lib/api";

type FieldErrors = Partial<Record<"name" | "slug" | "form", string>>;

export default function NewOrgPage() {
  const router = useRouter();
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors({});
    const data = new FormData(event.currentTarget);
    const parsed = createOrgSchema.safeParse({
      name: data.get("name"),
      slug: data.get("slug") || undefined,
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
      const org = await createOrg({
        name: parsed.data.name,
        slug: parsed.data.slug || undefined,
      });
      await switchOrg(org.slug);
      router.push(`/orgs/${org.slug}`);
      router.refresh();
    } catch (err) {
      const apiErr = err as ApiError;
      setErrors({ form: apiErr.detail ?? "Could not create organization" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-md space-y-6 px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Create organization</CardTitle>
            <CardDescription>
              Spin up a new workspace with you as the owner.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Field>
                <Label htmlFor="name">Name</Label>
                <Input id="name" name="name" required placeholder="Acme Inc." />
                <FieldError>{errors.name}</FieldError>
              </Field>
              <Field>
                <Label htmlFor="slug">Slug (optional)</Label>
                <Input
                  id="slug"
                  name="slug"
                  placeholder="acme"
                  pattern="[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
                />
                <FieldError>{errors.slug}</FieldError>
              </Field>
              <FieldError>{errors.form}</FieldError>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Creating…" : "Create organization"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </main>
  );
}
