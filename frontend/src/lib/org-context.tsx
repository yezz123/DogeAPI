"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { getMyRoleInOrg, type OrgSummary, type Role } from "@/lib/orgs";

type OrgContextValue = {
  org: OrgSummary | null;
  role: Role | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

const OrgContext = createContext<OrgContextValue | null>(null);

export function OrgContextProvider({
  slug,
  children,
}: {
  slug: string;
  children: ReactNode;
}) {
  const [org, setOrg] = useState<OrgSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setOrg(await getMyRoleInOrg(slug));
      setError(null);
    } catch (err) {
      setError((err as { detail?: string })?.detail ?? "Failed to load org");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  return (
    <OrgContext.Provider
      value={{
        org,
        role: org?.role ?? null,
        loading,
        error,
        refresh,
      }}
    >
      {children}
    </OrgContext.Provider>
  );
}

export function useOrgContext() {
  const ctx = useContext(OrgContext);
  if (!ctx) {
    throw new Error("useOrgContext must be used inside <OrgContextProvider>");
  }
  return ctx;
}
