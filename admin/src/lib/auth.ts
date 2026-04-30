import { apiFetch } from "@/lib/api";

export type User = {
  id: string;
  email: string;
  full_name: string | null;
  email_verified_at: string | null;
  is_superadmin: boolean;
  is_active: boolean;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type LoginInput = { email: string; password: string };

export const login = (input: LoginInput) =>
  apiFetch<TokenPair>("/auth/login", { method: "POST", json: input });

export const me = () => apiFetch<User>("/auth/me");

export const logout = () =>
  apiFetch<{ detail: string }>("/auth/logout", { method: "POST" });
