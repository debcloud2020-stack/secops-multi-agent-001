import { AgentRail } from "@/components/dashboard/agent-rail";
import { CostPanel } from "@/components/dashboard/cost-panel";
import { CveTable } from "@/components/dashboard/cve-table";
import { FindingsFeed } from "@/components/dashboard/findings-feed";
import { GuardrailFlags } from "@/components/dashboard/guardrail-flags";
import { PlanView } from "@/components/dashboard/plan-view";
import { SimilarIncidents } from "@/components/dashboard/similar-incidents";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RunStatus } from "@/lib/types";

/** All run panels driven by a RunStatus. Reused by the run page and history replay. */
export function RunResult({ run }: { run: RunStatus }) {
  return (
    <div className="space-y-4">
      <AgentRail visited={run.visited} status={run.status} />
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
