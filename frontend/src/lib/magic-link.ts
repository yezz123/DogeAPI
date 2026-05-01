import { apiFetch } from "@/lib/api";
import type { TokenPair, User } from "@/lib/auth";

export const requestMagicLink = (email: string) =>
  apiFetch<{ detail: string; link: string | null }>(
    "/auth/magic-link/request",
    { method: "POST", json: { email } },
  );

export const consumeMagicLink = (token: string) =>
  apiFetch<{ user: User; tokens: TokenPair }>("/auth/magic-link/consume", {
    method: "POST",
    json: { token },
  });
