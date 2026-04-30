import { apiFetch } from "@/lib/api";
import type { LoginInput, RegisterInput } from "@/lib/validators";

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

export type RegisterResponse = {
  user: User;
  tokens: TokenPair;
  email_verification_link: string | null;
};

export const login = (input: LoginInput) =>
  apiFetch<TokenPair>("/auth/login", { method: "POST", json: input });

export const register = (input: RegisterInput) =>
  apiFetch<RegisterResponse>("/auth/register", { method: "POST", json: input });

export const me = () => apiFetch<User>("/auth/me");

export const logout = () =>
  apiFetch<{ detail: string }>("/auth/logout", { method: "POST" });

export const verifyEmail = (token: string) =>
  apiFetch<{ detail: string }>("/auth/verify-email", {
    method: "POST",
    json: { token },
  });
