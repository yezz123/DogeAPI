import { apiFetch } from "@/lib/api";

export type AuditLogEntry = {
  id: string;
  org_id: string | null;
  actor_id: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  method: string;
  path: string;
  status_code: number;
  ip: string | null;
  user_agent: string | null;
  extra: Record<string, unknown>;
  created_at: string;
};

export const listAuditLog = (
  slug: string,
  params: { action?: string; limit?: number; offset?: number } = {},
) => {
  const query = new URLSearchParams();
  if (params.action) query.set("action", params.action);
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<AuditLogEntry[]>(`/orgs/${slug}/audit-log${suffix}`);
};
