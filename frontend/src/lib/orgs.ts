import { apiFetch } from "@/lib/api";
import type { TokenPair } from "@/lib/auth";

export type Role = "owner" | "admin" | "member";

export type OrgSummary = {
  id: string;
  slug: string;
  name: string;
  plan: string;
  created_at: string;
  role: Role;
};

export type Organization = {
  id: string;
  slug: string;
  name: string;
  plan: string;
  created_at: string;
};

export type Member = {
  user_id: string;
  email: string;
  full_name: string | null;
  role: Role;
  created_at: string;
};

export type Invitation = {
  id: string;
  org_id: string;
  email: string;
  role: Role;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
};

export type InvitationCreated = {
  invitation: Invitation;
  invite_link: string | null;
};

export const listOrgs = () => apiFetch<OrgSummary[]>("/orgs");

export const createOrg = (input: { name: string; slug?: string }) =>
  apiFetch<Organization>("/orgs", { method: "POST", json: input });

export const getOrg = (slug: string) => apiFetch<Organization>(`/orgs/${slug}`);

export const getMyRoleInOrg = (slug: string) =>
  apiFetch<OrgSummary>(`/orgs/${slug}/me`);

export const switchOrg = (slug: string) =>
  apiFetch<TokenPair>(`/orgs/${slug}/switch`, { method: "POST" });

export const listMembers = (slug: string) =>
  apiFetch<Member[]>(`/orgs/${slug}/members`);

export const changeMemberRole = (slug: string, userId: string, role: Role) =>
  apiFetch<{ id: string; role: Role }>(`/orgs/${slug}/members/${userId}`, {
    method: "PATCH",
    json: { role },
  });

export const removeMember = (slug: string, userId: string) =>
  apiFetch<void>(`/orgs/${slug}/members/${userId}`, { method: "DELETE" });

export const listInvitations = (slug: string) =>
  apiFetch<Invitation[]>(`/orgs/${slug}/invitations`);

export const createInvitation = (
  slug: string,
  input: { email: string; role: Role },
) =>
  apiFetch<InvitationCreated>(`/orgs/${slug}/invitations`, {
    method: "POST",
    json: input,
  });

export const revokeInvitation = (slug: string, invitationId: string) =>
  apiFetch<void>(`/orgs/${slug}/invitations/${invitationId}`, {
    method: "DELETE",
  });

export const acceptInvitation = (token: string) =>
  apiFetch<OrgSummary>("/invitations/accept", {
    method: "POST",
    json: { token },
  });
