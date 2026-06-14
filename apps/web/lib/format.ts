import type { DataMode, RunStatusValue, Severity } from "@/lib/types";

// One professional accent per data mode, reconciled with the Dark Intelligence palette:
// Live = emerald (real telemetry), Synthetic = violet (simulated), Mock = neutral slate.
// `badge` tints the mode badge; `border` is a left accent strip on result panels.
export const MODE_LABEL: Record<DataMode, string> = {
  mock: "Mock",
  live: "Live",
  synthetic: "Synthetic",
};

export const MODE_ACCENT: Record<DataMode, { badge: string; border: string }> = {
  mock: {
    badge: "bg-slate-400/10 text-slate-300 border-slate-400/30",
    border: "border-l-slate-400/50",
  },
  live: {
    badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
    border: "border-l-emerald-400/70",
  },
  synthetic: {
    badge: "bg-violet-500/15 text-violet-300 border-violet-500/40",
    border: "border-l-violet-400/70",
  },
};

// Severity mapped onto the functional accents (Red critical → Cyan low → neutral info).
export const SEVERITY_CLASS: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-300 border-red-500/40",
  high: "bg-orange-500/15 text-orange-300 border-orange-500/40",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  low: "bg-cyan-500/15 text-cyan-300 border-cyan-500/40",
  info: "bg-white/5 text-slate-300 border-white/15",
};

export const STATUS_LABEL: Record<RunStatusValue, string> = {
  queued: "Queued",
  running: "Running",
  awaiting_approval: "Awaiting approval",
  completed: "Completed",
  rejected: "Rejected",
  error: "Error",
};

// Status pills on the Dark Intelligence accents: Cyan=info/running, Amber=awaiting,
// Emerald=completed, Red=error/rejected.
export const STATUS_CLASS: Record<RunStatusValue, string> = {
  queued: "bg-white/5 text-slate-300 border-white/15",
  running: "bg-cyan-500/15 text-cyan-300 border-cyan-500/40",
  awaiting_approval: "bg-amber-500/15 text-amber-300 border-amber-500/40",
  completed: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
  rejected: "bg-red-500/15 text-red-300 border-red-500/40",
  error: "bg-red-500/15 text-red-300 border-red-500/40",
};

export function fmtScore(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return Number.isInteger(n) ? String(n) : n.toFixed(2);
}
