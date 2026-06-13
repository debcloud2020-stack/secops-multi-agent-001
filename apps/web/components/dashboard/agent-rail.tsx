"use client";

import { Check, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
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
          Agent rail
          <span className="text-sm font-normal text-muted-foreground">{pct}%</span>
        </CardTitle>
        <Progress value={pct} className="mt-1" />
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
                  "flex flex-col gap-1.5 rounded-lg border p-3 transition-colors",
                  done && "border-emerald-500/40 bg-emerald-500/5",
                  working && "border-sky-500/50 bg-sky-500/5",
                  !done && !working && "opacity-70",
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">Agent {i + 1}</span>
                  {done ? (
                    <Check className="size-4 text-emerald-500" />
                  ) : working ? (
                    <Loader2 className="size-4 animate-spin text-sky-500" />
                  ) : (
                    <span className="size-4" />
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
