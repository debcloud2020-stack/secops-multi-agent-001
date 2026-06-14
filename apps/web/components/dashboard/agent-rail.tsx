"use client";

import { Check, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AGENT_LABELS, AGENT_ORDER, type RunStatusValue } from "@/lib/types";
import { cn } from "@/lib/utils";

export function AgentRail({
  visited,
  status,
}: {
  visited: string[];
  status?: RunStatusValue;
}) {
  const visitedSet = new Set(visited);
  const active = status === "running" || status === "queued";
  // The first not-yet-visited agent is the one currently working (while running).
  const current = AGENT_ORDER.find((a) => !visitedSet.has(a));
  const pct = Math.round((visited.filter((a) => AGENT_ORDER.includes(a as never)).length / AGENT_ORDER.length) * 100);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            {active && (
              <span className="size-2 animate-pulse rounded-full bg-cyan-400 text-cyan-400 shadow-[0_0_8px_currentColor]" />
            )}
            Live Scan Progress
          </span>
          <span className="font-mono text-sm font-normal tabular-nums text-cyan-300">{pct}%</span>
        </CardTitle>
        {/* Animated gradient scan bar */}
        <div className="relative mt-2 h-2 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400 transition-[width] duration-500 ease-out"
            style={{ width: `${pct}%` }}
          />
          {active && (
            <div className="pointer-events-none absolute inset-y-0 left-0 w-1/3 animate-scan-shimmer bg-gradient-to-r from-transparent via-white/40 to-transparent" />
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ol className="grid gap-2 sm:grid-cols-5">
          {AGENT_ORDER.map((agent, i) => {
            const done = visitedSet.has(agent);
            const working = active && agent === current;
            return (
              <li
                key={agent}
                className={cn(
                  "flex flex-col gap-1.5 rounded-xl border p-3 transition-all duration-200",
                  done && "border-emerald-500/40 bg-emerald-500/10",
                  working && "border-cyan-500/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/10",
                  !done && !working && "border-white/10 bg-white/[0.02] opacity-60",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">Agent {i + 1}</span>
                  {done ? (
                    <Check className="size-4 text-emerald-400" />
                  ) : working ? (
                    <Loader2 className="size-4 animate-spin text-cyan-400" />
                  ) : (
                    <span className="size-2 self-center rounded-full bg-white/20" />
                  )}
                </div>
                <span className="text-sm font-medium leading-tight">{AGENT_LABELS[agent] ?? agent}</span>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
