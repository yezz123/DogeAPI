import { apiFetch } from "@/lib/api";

export type Subscription = {
  plan: string;
  status: string;
  current_period_end: string | null;
  limits: {
    max_members: number | null;
    max_api_keys: number | null;
    monthly_ai_tokens: number | null;
  };
};

export type Usage = {
  members: number;
  api_keys: number;
};

export const getSubscription = (slug: string) =>
  apiFetch<Subscription>(`/orgs/${slug}/billing/subscription`);

export const getUsage = (slug: string) =>
  apiFetch<Usage>(`/orgs/${slug}/billing/usage`);

export const startCheckout = (slug: string, plan: string) =>
  apiFetch<{ url: string }>(`/orgs/${slug}/billing/checkout`, {
    method: "POST",
    json: { plan },
  });

export const openPortal = (slug: string) =>
  apiFetch<{ url: string }>(`/orgs/${slug}/billing/portal`, { method: "POST" });
