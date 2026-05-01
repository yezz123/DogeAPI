"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { acceptInvitation } from "@/lib/orgs";
import { me } from "@/lib/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/lib/api";

type Status = "pending" | "ok" | "error" | "needs_login";

function AcceptInviteInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token");
  const [status, setStatus] = useState<Status>("pending");
  const [error, setError] = useState<string | null>(null);
  const [orgSlug, setOrgSlug] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Missing invitation token");
      return;
    }
    (async () => {
      try {
        await me();
      } catch {
        setStatus("needs_login");
        sessionStorage.setItem("pending_invite", token);
        return;
      }
      try {
        const org = await acceptInvitation(token);
        setOrgSlug(org.slug);
        setStatus("ok");
      } catch (err) {
        const apiErr = err as ApiError;
        setStatus("error");
        setError(apiErr.detail ?? "Could not accept invitation");
      }
    })();
  }, [token]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {status === "pending" && "Accepting invitation…"}
          {status === "ok" && "You're in!"}
          {status === "needs_login" && "Sign in to accept"}
          {status === "error" && "Could not accept invitation"}
        </CardTitle>
        <CardDescription>
          {status === "pending" && "Hang tight while we add you to the org."}
          {status === "ok" && "You've joined the organization."}
          {status === "needs_login" &&
            "Sign in or create an account to accept this invitation."}
          {status === "error" && (error ?? "Try requesting a new invitation.")}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {status === "ok" && orgSlug && (
          <Button onClick={() => router.push(`/orgs/${orgSlug}`)}>
            Go to organization
          </Button>
        )}
        {status === "needs_login" && (
          <div className="flex gap-2">
            <Link
              href="/login"
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-md border border-border px-4 py-2 text-sm font-medium"
            >
              Create account
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function AcceptInvitePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="w-full"
      >
        <Suspense
          fallback={
            <Card>
              <CardHeader>
                <CardTitle>Loading invitation…</CardTitle>
              </CardHeader>
            </Card>
          }
        >
          <AcceptInviteInner />
        </Suspense>
      </motion.div>
    </main>
  );
}
