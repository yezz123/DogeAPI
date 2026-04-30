import { apiFetch } from "@/lib/api";

export const requestPasswordReset = (email: string) =>
  apiFetch<{ detail: string; link: string | null }>(
    "/auth/password-reset/request",
    { method: "POST", json: { email } },
  );

export const consumePasswordReset = (token: string, new_password: string) =>
  apiFetch<{ detail: string }>("/auth/password-reset/consume", {
    method: "POST",
    json: { token, new_password },
  });
