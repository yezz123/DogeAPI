import { apiFetch } from "@/lib/api";

export type APIKey = {
  id: string;
  org_id: string;
  name: string;
  prefix: string;
  scopes: string[];
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
};

export type APIKeyCreated = {
  api_key: APIKey;
  plaintext_key: string;
};

export const listApiKeys = (slug: string) =>
  apiFetch<APIKey[]>(`/orgs/${slug}/api-keys`);

export const createApiKey = (
  slug: string,
  input: { name: string; scopes: string[]; expires_at?: string | null },
) =>
  apiFetch<APIKeyCreated>(`/orgs/${slug}/api-keys`, {
    method: "POST",
    json: input,
  });

export const revokeApiKey = (slug: string, keyId: string) =>
  apiFetch<void>(`/orgs/${slug}/api-keys/${keyId}`, { method: "DELETE" });

export const ALL_SCOPES = [
  "org:read",
  "org:write",
  "org:members:read",
  "org:members:write",
  "org:invitations:read",
  "org:invitations:write",
  "org:apikeys:read",
  "org:apikeys:write",
  "org:audit:read",
  "org:billing:read",
  "org:ai:use",
  "org:ai:write",
] as const;
