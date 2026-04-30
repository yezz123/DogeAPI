"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  getSubscription,
  getUsage,
  openPortal,
  startCheckout,
  type Subscription,
  type Usage,
} from "@/lib/billing";
import { useOrgContext } from "@/lib/org-context";
import { canManageBilling } from "@/lib/permissions";
import { readPublicFlag } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ApiError } from "@/lib/api";

const PLANS: Array<{ id: "pro" | "enterprise"; name: string; price: string }> =
  [
    { id: "pro", name: "Pro", price: "$49/mo" },
    { id: "enterprise", name: "Enterprise", price: "Custom" },
  ];

export default function BillingPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug as string;
  const { role } = useOrgContext();
  const canManage = role ? canManageBilling(role) : false;
  const stripeEnabled = readPublicFlag("FEATURE_STRIPE");
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!slug || !stripeEnabled) return;
    Promise.all([getSubscription(slug), getUsage(slug)])
      .then(([sub, u]) => {
        setSubscription(sub);
        setUsage(u);
      })
      .catch((err: ApiError) =>
        setError(err.detail ?? "Failed to load billing"),
      );
  }, [slug, stripeEnabled]);

  if (!stripeEnabled) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Billing</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Stripe billing is disabled in this environment.
        </CardContent>
      </Card>
    );
  }

  async function handleCheckout(plan: "pro" | "enterprise") {
    setBusy(true);
    try {
      const { url } = await startCheckout(slug, plan);
      window.location.assign(url);
    } catch (err) {
      setError((err as ApiError).detail ?? "Could not start checkout");
    } finally {
      setBusy(false);
    }
  }

  async function handlePortal() {
    setBusy(true);
    try {
      const { url } = await openPortal(slug);
      window.location.assign(url);
    } catch (err) {
      setError((err as ApiError).detail ?? "Could not open portal");
    } finally {
      setBusy(false);
    }
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6"
    >
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Billing</h1>
        <p className="text-sm text-muted-foreground">
          Plans and limits for this organization.
        </p>
      </header>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {subscription && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current plan</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-semibold capitalize">
                {subscription.plan}
              </span>
              <span className="rounded-full border border-border px-2 py-0.5 text-xs uppercase tracking-wider text-muted-foreground">
                {subscription.status}
              </span>
            </div>
            <dl className="grid grid-cols-2 gap-2 text-muted-foreground">
              <dt>Members</dt>
              <dd>
                {usage?.members ?? "—"} /{" "}
                {subscription.limits.max_members ?? "∞"}
              </dd>
              <dt>API keys</dt>
              <dd>
                {usage?.api_keys ?? "—"} /{" "}
                {subscription.limits.max_api_keys ?? "∞"}
              </dd>
              <dt>Monthly AI tokens</dt>
              <dd>{subscription.limits.monthly_ai_tokens ?? "Unlimited"}</dd>
              {subscription.current_period_end && (
                <>
                  <dt>Renews</dt>
                  <dd>
                    {new Date(
                      subscription.current_period_end,
                    ).toLocaleDateString()}
                  </dd>
                </>
              )}
            </dl>
            {canManage && (
              <div className="flex gap-2 pt-2">
                <Button
                  onClick={handlePortal}
                  variant="secondary"
                  disabled={busy}
                >
                  Manage billing
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {canManage && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Upgrade</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                className="flex items-center justify-between rounded-md border border-border p-4"
              >
                <div>
                  <p className="font-semibold">{plan.name}</p>
                  <p className="text-sm text-muted-foreground">{plan.price}</p>
                </div>
                <Button
                  size="sm"
                  onClick={() => handleCheckout(plan.id)}
                  disabled={busy || subscription?.plan === plan.id}
                >
                  {subscription?.plan === plan.id ? "Current" : "Choose"}
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </motion.section>
  );
}
