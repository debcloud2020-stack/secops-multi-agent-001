"use client";

import { History, LayoutDashboard, ListChecks, PlayCircle, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/run", label: "Run", icon: PlayCircle },
  { href: "/dashboard/threats", label: "Threats", icon: ShieldAlert },
  { href: "/dashboard/compliance", label: "Compliance", icon: ListChecks },
  { href: "/dashboard/history", label: "History", icon: History },
];

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <aside className="flex w-full shrink-0 flex-col gap-1 border-b border-white/10 bg-white/[0.03] p-3 backdrop-blur-xl md:h-dvh md:w-60 md:border-r md:border-b-0">
      <Link href="/" className="mb-4 flex items-center gap-2.5 px-2 py-1.5">
        <span className="inline-flex size-8 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-emerald-400 text-[#06121a] shadow-lg shadow-cyan-500/20">
          <ShieldAlert className="size-4" />
        </span>
        <span className="font-heading text-base font-semibold tracking-tight text-foreground">
          SecOps
        </span>
      </Link>
      <nav className="flex flex-row gap-1 md:flex-col">
        {LINKS.map((l) => {
          const active = pathname === l.href;
          return (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                active
                  ? "border border-cyan-500/30 bg-cyan-500/10 text-cyan-200"
                  : "border border-transparent text-muted-foreground hover:bg-white/5 hover:text-foreground",
              )}
            >
              <l.icon className="size-4" />
              <span className="hidden sm:inline">{l.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
