import type { RunStatusValue, Severity } from "@/lib/types";

export const SEVERITY_CLASS: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/30",
  high: "bg-orange-500/15 text-orange-600 dark:text-orange-400 border-orange-500/30",
  medium: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  low: "bg-sky-500/15 text-sky-600 dark:text-sky-400 border-sky-500/30",
  info: "bg-muted text-muted-foreground border-border",
};

export const STATUS_LABEL: Record<RunStatusValue, string> = {
  queued: "Queued",
  running: "Running",
  awaiting_approval: "Awaiting approval",
  completed: "Completed",
  rejected: "Rejected",
  error: "Error",
};

export const STATUS_CLASS: Record<RunStatusValue, string> = {
  queued: "bg-muted text-muted-foreground border-border",
  running: "bg-sky-500/15 text-sky-600 dark:text-sky-400 border-sky-500/30",
  awaiting_approval: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  completed: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  rejected: "bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/30",
  error: "bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/30",
};

export function fmtScore(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return Number.isInteger(n) ? String(n) : n.toFixed(2);
}
