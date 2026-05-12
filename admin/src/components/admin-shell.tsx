"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { logout, me, type User } from "@/lib/auth";
import { AdminSidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { AdminError, AdminLoading } from "@/components/admin-state";
import type { ApiError } from "@/lib/api";

export function AdminShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    me()
      .then((u) => {
        if (!u.is_superadmin) {
          router.replace("/login");
          return;
        }
        setUser(u);
      })
      .catch((err: ApiError) => {
        if (err.status === 401) router.replace("/login");
        else setError(err.detail ?? "Failed to load profile");
      });
  }, [router]);

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // ignore
    }
    router.replace("/login");
  }

  if (error) {
    return <AdminError message={error} />;
  }

  if (!user) {
    return <AdminLoading label="Authorizing operator" />;
  }

  return (
    <main className="min-h-screen px-4 py-4 text-foreground sm:px-6">
      <section className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-7xl gap-5 rounded-4xl border border-border bg-background/82 p-4 backdrop-blur-md lg:grid-cols-[18rem_1fr] lg:p-5">
        <aside className="flex flex-col overflow-hidden rounded-3xl bg-foreground p-5 text-background">
          <div className="border-b border-background/15 pb-5">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.32em] text-primary">
              Operator console
            </p>
            <h1 className="mt-2 text-xl font-semibold tracking-tight">
              AI Template Admin
            </h1>
          </div>
          <AdminSidebar />
          <div className="mt-5 flex items-center justify-between gap-3 border-t border-background/15 pt-4 text-xs text-background/62 lg:mt-auto lg:block lg:space-y-3">
            <div>
              <p className="text-[0.62rem] uppercase tracking-[0.22em] text-primary">
                Signed in
              </p>
              <p className="mt-1 truncate font-mono">{user.email}</p>
            </div>
            <Button
              onClick={handleLogout}
              variant="ghost"
              size="sm"
              className="shrink-0 text-background hover:bg-background/10 lg:w-full"
            >
              Sign out
            </Button>
          </div>
        </aside>
        <section className="min-w-0 rounded-3xl border border-border bg-muted/44 p-5 sm:p-6 lg:p-8">
          {children}
        </section>
      </section>
    </main>
  );
}
