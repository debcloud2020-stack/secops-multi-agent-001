import type { DataMode, RunStatusValue, Severity } from "@/lib/types";

// One professional accent per data mode (slate / emerald / violet) over the neutral base.
// `badge` tints the mode badge; `border` is a subtle left accent strip on result panels.
export const MODE_LABEL: Record<DataMode, string> = {
  mock: "Mock",
  live: "Live",
  synthetic: "Synthetic",
};

export const MODE_ACCENT: Record<DataMode, { badge: string; border: string }> = {
  mock: {
    badge: "bg-slate-500/15 text-slate-600 dark:text-slate-300 border-slate-500/30",
    border: "border-l-slate-500/50",
  },
  live: {
    badge: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    border: "border-l-emerald-500/60",
  },
  synthetic: {
    badge: "bg-violet-500/15 text-violet-600 dark:text-violet-400 border-violet-500/30",
    border: "border-l-violet-500/60",
  },
};

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
