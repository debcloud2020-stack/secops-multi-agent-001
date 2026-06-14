import { AgentRail } from "@/components/dashboard/agent-rail";
import { CostPanel } from "@/components/dashboard/cost-panel";
import { CveTable } from "@/components/dashboard/cve-table";
import { FindingsFeed } from "@/components/dashboard/findings-feed";
import { GuardrailFlags } from "@/components/dashboard/guardrail-flags";
import { PlanView } from "@/components/dashboard/plan-view";
import { SimilarIncidents } from "@/components/dashboard/similar-incidents";
import { SourceRowsPanel } from "@/components/dashboard/source-rows";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DataMode, RunStatus } from "@/lib/types";

/** All run panels driven by a RunStatus. Reused by the run page and history replay. */
export function RunResult({ run, mode }: { run: RunStatus; mode?: DataMode }) {
  const notices = run.data_notices ?? [];
  return (
    <div className="space-y-4">
      {notices.length > 0 && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/5 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
          <p className="font-medium">Fell back to mock data</p>
          <ul className="mt-1 list-disc space-y-0.5 pl-5 text-amber-700/90 dark:text-amber-300/90">
            {notices.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
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
          <CveTable rows={run.cve_matches} />
        </CardContent>
      </Card>
    </div>
  );
}
