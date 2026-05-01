import type { Role } from "@/lib/orgs";
import { ALL_SCOPES } from "@/lib/api-keys";

const ROLE_SCOPES: Record<Role, string[]> = {
  owner: ["org:*"],
  admin: [
    "org:read",
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
  ],
  member: ["org:read", "org:members:read", "org:ai:use"],
};

function scopeMatches(required: string, granted: string): boolean {
  if (granted === required) return true;
  if (granted.endsWith(":*")) {
    const prefix = granted.slice(0, -1);
    return required.startsWith(prefix);
  }
  return false;
}

export function scopesAvailableTo(role: Role): readonly string[] {
  const granted = ROLE_SCOPES[role];
  return ALL_SCOPES.filter((scope) =>
    granted.some((g) => scopeMatches(scope, g)),
  );
}
