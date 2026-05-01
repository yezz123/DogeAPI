"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { consumeMagicLink } from "@/lib/magic-link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ApiError } from "@/lib/api";

type Status = "pending" | "ok" | "error";

function MagicLinkInner() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token");
  const [status, setStatus] = useState<Status>("pending");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Missing token");
      return;
    }
    consumeMagicLink(token)
      .then(() => setStatus("ok"))
      .catch((err: ApiError) => {
        setStatus("error");
        setError(err.detail ?? "Could not sign you in");
      });
  }, [token]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {status === "pending" && "Signing you in…"}
          {status === "ok" && "Welcome back"}
          {status === "error" && "Sign-in failed"}
        </CardTitle>
        <CardDescription>
          {status === "pending" && "Verifying your magic link."}
          {status === "ok" && "You're now signed in."}
          {status === "error" && (error ?? "Request a new link.")}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex gap-2">
        {status === "ok" && (
          <Button onClick={() => router.push("/dashboard")}>
            Go to dashboard
          </Button>
        )}
        {status === "error" && (
          <Link
            href="/login"
            className="rounded-md border border-border px-4 py-2 text-sm font-medium"
          >
            Back to sign in
          </Link>
        )}
      </CardContent>
    </Card>
  );
}

export default function MagicLinkPage() {
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
                <CardTitle>Signing you in…</CardTitle>
              </CardHeader>
            </Card>
          }
        >
          <MagicLinkInner />
        </Suspense>
      </motion.div>
    </main>
  );
}
