"use client";

import { useEffect, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { logout, me, type User } from "@/lib/auth";
import { AdminSidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
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
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-destructive">{error}</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </main>
    );
  }

  return (
    <div className="grid min-h-screen grid-cols-[220px,1fr]">
      <aside className="border-r border-border bg-muted p-4">
        <div className="mb-6">
          <p className="text-xs uppercase tracking-widest text-accent">
            Operator console
          </p>
          <h1 className="text-lg font-semibold">AI Template Admin</h1>
        </div>
        <AdminSidebar />
        <div className="mt-8 space-y-2 border-t border-border pt-4 text-xs text-muted-foreground">
          <p>{user.email}</p>
          <Button
            onClick={handleLogout}
            variant="ghost"
            size="sm"
            className="w-full"
          >
            Sign out
          </Button>
        </div>
      </aside>
      <main className="p-8">{children}</main>
    </div>
  );
}
