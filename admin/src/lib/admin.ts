import { apiFetch } from "@/lib/api";

export type Tenant = {
  id: string;
  slug: string;
  name: string;
  plan: string;
  member_count: number;
  created_at: string;
};

export type AdminUser = {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superadmin: boolean;
  email_verified_at: string | null;
  created_at: string;
};

export type AuditEntry = {
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

export type SystemHealth = {
  db_ok: boolean;
  redis_ok: boolean;
  total_users: number;
  total_orgs: number;
  total_api_keys: number;
};

export const listTenants = (limit = 50, offset = 0) =>
  apiFetch<Tenant[]>(`/admin/tenants?limit=${limit}&offset=${offset}`);

export const getTenant = (id: string) =>
  apiFetch<Tenant>(`/admin/tenants/${id}`);

export const listUsers = (params: { email?: string } = {}) => {
  const q = new URLSearchParams();
  if (params.email) q.set("email", params.email);
  q.set("limit", "100");
  return apiFetch<AdminUser[]>(`/admin/users?${q.toString()}`);
};

export const listAuditLog = (
  params: { org_id?: string; action?: string } = {},
) => {
  const q = new URLSearchParams();
  if (params.org_id) q.set("org_id", params.org_id);
  if (params.action) q.set("action", params.action);
  q.set("limit", "100");
  return apiFetch<AuditEntry[]>(`/admin/audit-log?${q.toString()}`);
};

export const getSystemHealth = () =>
  apiFetch<SystemHealth>("/admin/system-health");
