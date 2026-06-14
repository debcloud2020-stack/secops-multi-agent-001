import { AlertTriangle } from "lucide-react";

import { AgentRail } from "@/components/dashboard/agent-rail";
import { CostPanel } from "@/components/dashboard/cost-panel";
import { CveTable } from "@/components/dashboard/cve-table";
import { CvssGauge } from "@/components/dashboard/cvss-gauge";
import { FindingsFeed } from "@/components/dashboard/findings-feed";
import { GuardrailFlags } from "@/components/dashboard/guardrail-flags";
import { PlanView } from "@/components/dashboard/plan-view";
import { SimilarIncidents } from "@/components/dashboard/similar-incidents";
import { SourceRowsPanel } from "@/components/dashboard/source-rows";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CVEMatch, DataMode, RunStatus } from "@/lib/types";

/** Highest-CVSS CVE in the run, for the Threat Intel risk gauge. */
function topCve(rows: CVEMatch[]): CVEMatch | null {
  const scored = rows.filter((c) => typeof c.cvss === "number");
  if (scored.length === 0) return null;
  return scored.reduce((a, b) => ((b.cvss ?? 0) > (a.cvss ?? 0) ? b : a));
}

/** All run panels driven by a RunStatus. Reused by the run page and history replay. */
export function RunResult({
  run,
  mode,
  incidentTitle,
}: {
  run: RunStatus;
  mode?: DataMode;
  incidentTitle?: string;
}) {
  const notices = run.data_notices ?? [];
  const top = topCve(run.cve_matches);
  const evidenceRows = run.source_rows?.count ?? 0;
  const planCount = run.plan ? 1 : 0;

  return (
    <div className="space-y-4">
      {/* Incident header + cardinality strip */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-4 backdrop-blur-xl">
        <h2 className="font-heading text-lg font-semibold tracking-tight">
          <span className="text-muted-foreground">Investigating:</span>{" "}
          <span className="font-mono text-cyan-300">{run.incident_id}</span>
          {incidentTitle && <span className="text-foreground"> · {incidentTitle}</span>}
        </h2>
        <p className="mt-1 text-xs text-muted-foreground">
          1 incident <span className="text-white/20">·</span> {evidenceRows} evidence rows{" "}
          <span className="text-white/20">·</span> {run.findings.length} findings{" "}
          <span className="text-white/20">·</span> {planCount} response plan
        </p>
      </div>

      {notices.length > 0 && (
        <div className="flex gap-3 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-400" />
          <div>
            <p className="font-medium">Fell back to mock data</p>
            <ul className="mt-1 list-disc space-y-0.5 pl-5 text-amber-200/90">
              {notices.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
      <AgentRail visited={run.visited} status={run.status} />
      {run.source_rows && <SourceRowsPanel data={run.source_rows} mode={mode} />}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-4">
          <FindingsFeed findings={run.findings} />
          <PlanView plan={run.plan} />
        </div>
        <div className="space-y-4">
          <CostPanel cost={run.cost} />
          <GuardrailFlags flags={run.guardrail_flags} />
          <SimilarIncidents items={run.similar_past} />
        </div>
      </div>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">CVE matches</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
            {top && (
              <div className="flex shrink-0 flex-col items-center gap-1 rounded-xl border border-white/10 bg-white/[0.02] p-4 lg:w-48">
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Top threat
                </span>
                <CvssGauge score={top.cvss ?? 0} cveId={top.cve_id} />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <CveTable rows={run.cve_matches} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
