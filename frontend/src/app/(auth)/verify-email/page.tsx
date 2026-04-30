"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { verifyEmail } from "@/lib/auth";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { ApiError } from "@/lib/api";

type Status = "pending" | "ok" | "error";

function VerifyEmailInner() {
  const params = useSearchParams();
  const token = params.get("token");
  const [status, setStatus] = useState<Status>("pending");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setError("Missing verification token");
      return;
    }
    verifyEmail(token)
      .then(() => setStatus("ok"))
      .catch((err: ApiError) => {
        setStatus("error");
        setError(err.detail ?? "Could not verify email");
      });
  }, [token]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {status === "pending" && "Verifying email…"}
          {status === "ok" && "Email verified"}
          {status === "error" && "Verification failed"}
        </CardTitle>
        <CardDescription>
          {status === "pending" && "Hang tight while we confirm your address."}
          {status === "ok" && "Your email is confirmed. You can now sign in."}
          {status === "error" && (error ?? "Try requesting a new link.")}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Link
          href={status === "ok" ? "/dashboard" : "/login"}
          className="text-sm font-medium text-primary hover:underline"
        >
          {status === "ok" ? "Continue to dashboard →" : "Back to sign in →"}
        </Link>
      </CardContent>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
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
              <CardTitle>Verifying email…</CardTitle>
            </CardHeader>
          </Card>
        }
      >
        <VerifyEmailInner />
      </Suspense>
    </motion.div>
  );
}
