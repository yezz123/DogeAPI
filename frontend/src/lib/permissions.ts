import type { Role } from "@/lib/orgs";

export const canManageMembers = (role: Role): boolean =>
  role === "owner" || role === "admin";

export const canManageInvitations = (role: Role): boolean =>
  role === "owner" || role === "admin";

export const canEditOrg = (role: Role): boolean => role === "owner";

export const canManageBilling = (role: Role): boolean => role === "owner";

export const canManageApiKeys = (role: Role): boolean =>
  role === "owner" || role === "admin";

export const canViewAuditLog = (role: Role): boolean =>
  role === "owner" || role === "admin";
