"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Overview", meta: "Health and activity" },
  { href: "/tenants", label: "Tenants", meta: "Organizations" },
  { href: "/users", label: "Users", meta: "Accounts" },
  { href: "/audit-log", label: "Audit log", meta: "Mutations" },
  { href: "/system-health", label: "System health", meta: "Dependencies" },
];

export function AdminSidebar() {
  const pathname = usePathname();
  return (
    <nav className="mt-5 flex gap-2 overflow-x-auto pb-1 lg:grid lg:gap-1.5 lg:overflow-visible lg:pb-0">
      {NAV.map((item) => {
        const active =
          pathname === item.href ||
          (item.href !== "/dashboard" && pathname?.startsWith(item.href));
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "min-w-40 rounded-2xl border px-3.5 py-3 transition lg:min-w-0",
              active
                ? "border-background/20 bg-background text-foreground"
                : "border-transparent text-background/62 hover:border-background/15 hover:bg-background/10 hover:text-background",
            )}
          >
            <span className="flex items-center gap-2 text-sm font-semibold">
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  active ? "bg-primary" : "bg-background/28",
                )}
              />
              {item.label}
            </span>
            <span className="mt-1 block pl-3.5 text-xs opacity-70">
              {item.meta}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
