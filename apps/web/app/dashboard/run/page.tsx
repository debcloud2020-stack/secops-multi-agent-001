"use client";

import { Play } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { ApprovalPanel } from "@/components/dashboard/approval-panel";
import { DataModeToggle } from "@/components/dashboard/data-mode-toggle";
import { ModeBadge } from "@/components/dashboard/mode-badge";
import { PageHeader } from "@/components/dashboard/page-header";
import { RunResult } from "@/components/dashboard/run-result";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getIncidents } from "@/lib/api";
import { useRun } from "@/hooks/use-run";
import { MODE_ACCENT, MODE_LABEL } from "@/lib/format";
import type { DataMode, IncidentOut, RunStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function RunPage() {
  const [incidents, setIncidents] = useState<IncidentOut[]>([]);
  const [selected, setSelected] = useState("");
  const [mode, setMode] = useState<DataMode>("mock");
  // Most recent run per mode (in-memory; resets on refresh) so each toggle shows its own
  // result and never another mode's stale data.
  const [results, setResults] = useState<Partial<Record<DataMode, RunStatus>>>({});
  const [seenRun, setSeenRun] = useState<RunStatus | null>(null);
  const { run, error, polling, start, approve } = useRun();

  // Remember each active-run snapshot under its own mode. Guarded setState-during-render
  // (React's "storing info from previous renders" pattern) — fires once per new run object.
  if (run !== seenRun) {
    setSeenRun(run);
    if (run?.data_mode) {
      setResults((prev) => ({ ...prev, [run.data_mode as DataMode]: run }));
    }
  }

  useEffect(() => {
    getIncidents()
      .then((list) => {
        setIncidents(list);
        setSelected((s) => s || list[0]?.id || "");
      })
      .catch(() => toast.error("Failed to load incidents"));
  }, []);

  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

  const incident = incidents.find((i) => i.id === selected);
  const inFlight = polling || run?.status === "awaiting_approval";
  // Show the live active run when it matches the selected toggle, else that mode's frozen run.
  const displayed = run?.data_mode === mode ? run : results[mode] ?? null;
  // The approval panel must target the active poller, so only offer it when the displayed
  // run IS the active run (approve() resumes the active run id).
  const canApprove =
    displayed?.status === "awaiting_approval" && displayed.run_id === run?.run_id;

  return (
    <>
      <PageHeader
        title="Run an investigation"
        description="Pick a curated incident, then watch the five-agent rail progress via polling."
        actions={
          <Button onClick={() => selected && start(selected, mode)} disabled={!selected || inFlight}>
            <Play className="size-4" /> {polling ? "Running…" : "Run"}
          </Button>
        }
      />

      <div className="space-y-4 p-6">
        <Card>
          <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-medium">Incident</label>
              <Select
                value={selected}
                onValueChange={(v) => setSelected(v ?? "")}
                disabled={inFlight}
              >
                <SelectTrigger className="w-full sm:max-w-md">
                  <SelectValue placeholder="Select a curated incident" />
                </SelectTrigger>
                <SelectContent>
                  {incidents.map((i) => (
                    <SelectItem key={i.id} value={i.id}>
                      {i.title}
                      {i.requires_approval ? "  · approval" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {incident && (
                <p className="text-sm text-muted-foreground">{incident.description}</p>
              )}
            </div>
            <DataModeToggle value={mode} onChange={setMode} />
          </CardContent>
        </Card>

        {displayed ? (
          <div className="space-y-4">
            <div
              className={cn(
                "flex items-center gap-3 rounded-lg border border-l-4 px-4 py-2.5",
                MODE_ACCENT[mode].border,
              )}
            >
              <ModeBadge mode={mode} />
              <span className="font-mono text-sm text-muted-foreground">
                run {displayed.run_id.slice(0, 8)}
              </span>
              <span className="ml-auto">
                <StatusBadge status={displayed.status} />
              </span>
            </div>
            {canApprove && <ApprovalPanel onDecision={(d, ep) => approve(d, ep)} />}
            <RunResult run={displayed} mode={mode} />
          </div>
        ) : (
          <div className="rounded-xl border border-dashed p-12 text-center text-sm text-muted-foreground">
            No <span className="font-medium">{MODE_LABEL[mode]}</span> run yet — press{" "}
            <span className="font-medium">Run</span> to investigate in {MODE_LABEL[mode]} mode and
            load its data. Results appear only after running this mode.
          </div>
        )}
      </div>
    </>
  );
}
