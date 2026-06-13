"use client";

import { Play } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { ApprovalPanel } from "@/components/dashboard/approval-panel";
import { DataModeToggle } from "@/components/dashboard/data-mode-toggle";
import { PageHeader } from "@/components/dashboard/page-header";
import { RunResult } from "@/components/dashboard/run-result";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { usePassword } from "@/components/providers/password-provider";
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
import type { DataMode, IncidentOut } from "@/lib/types";

export default function RunPage() {
  const { authed } = usePassword();
  const [incidents, setIncidents] = useState<IncidentOut[]>([]);
  const [selected, setSelected] = useState("");
  const [mode, setMode] = useState<DataMode>("mock");
  const { run, error, polling, start, approve } = useRun();

  useEffect(() => {
    if (!authed) return;
    getIncidents()
      .then((list) => {
        setIncidents(list);
        setSelected((s) => s || list[0]?.id || "");
      })
      .catch(() => toast.error("Failed to load incidents"));
  }, [authed]);

  useEffect(() => {
    if (error) toast.error(error);
  }, [error]);

  const incident = incidents.find((i) => i.id === selected);
  const inFlight = polling || run?.status === "awaiting_approval";

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

        {run ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <StatusBadge status={run.status} />
              <span className="text-sm text-muted-foreground">run {run.run_id.slice(0, 8)}</span>
            </div>
            {run.status === "awaiting_approval" && (
              <ApprovalPanel onDecision={(d, ep) => approve(d, ep)} />
            )}
            <RunResult run={run} />
          </div>
        ) : (
          <div className="rounded-xl border border-dashed p-12 text-center text-sm text-muted-foreground">
            No run yet — choose an incident and press <span className="font-medium">Run</span>.
          </div>
        )}
      </div>
    </>
  );
}
