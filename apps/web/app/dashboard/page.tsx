"use client";

import { Activity, ListChecks, ShieldAlert, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { PageHeader } from "@/components/dashboard/page-header";
import { usePassword } from "@/components/providers/password-provider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getCompliance, getIncidents, getRun, getThreats, listRuns } from "@/lib/api";
import type { ComplianceOut, CVEMatch, IncidentOut, RunSummary } from "@/lib/types";

interface Kpis {
  openIncidents: number;
  criticalKev: number;
  compliancePct: number;
  recentRuns: number;
  spend: number;
}

export default function OverviewPage() {
  const { authed } = usePassword();
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [coverage, setCoverage] = useState<{ name: string; coverage: number }[]>([]);

  useEffect(() => {
    if (!authed) return;
    (async () => {
      const [incidents, threats, compliance, runs] = await Promise.all([
        getIncidents().catch(() => [] as IncidentOut[]),
        getThreats().catch(() => [] as CVEMatch[]),
        getCompliance().catch(() => ({ frameworks: [] }) as ComplianceOut),
        listRuns().catch(() => [] as RunSummary[]),
      ]);
      const pct =
        compliance.frameworks.length > 0
          ? Math.round(
              compliance.frameworks.reduce((s, f) => s + f.coverage_pct, 0) /
                compliance.frameworks.length,
            )
          : 0;
      let spend = 0;
      if (runs.length > 0) {
        const latest = await getRun(runs[runs.length - 1].run_id).catch(() => null);
        spend = latest?.cost?.total ?? 0;
      }
      setKpis({
        openIncidents: incidents.length,
        criticalKev: threats.filter((t) => t.in_kev && t.priority >= 8).length,
        compliancePct: pct,
        recentRuns: runs.length,
        spend,
      });
      setCoverage(compliance.frameworks.map((f) => ({ name: f.name, coverage: f.coverage_pct })));
    })();
  }, [authed]);

  const cards = [
    { label: "Curated incidents", value: kpis?.openIncidents, icon: Activity },
    { label: "Critical KEV CVEs", value: kpis?.criticalKev, icon: ShieldAlert },
    { label: "Compliance", value: kpis ? `${kpis.compliancePct}%` : undefined, icon: ListChecks },
    { label: "Recent runs", value: kpis?.recentRuns, icon: ShieldCheck },
    { label: "Spend (last run)", value: kpis ? `${kpis.spend} tok` : undefined, icon: Activity },
  ];

  return (
    <>
      <PageHeader title="Overview" description="Live posture across incidents, threats, and compliance." />
      <div className="space-y-4 p-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {cards.map((c) => (
            <Card key={c.label}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-sm font-medium text-muted-foreground">
                  {c.label}
                  <c.icon className="size-4" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                {c.value === undefined ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <div className="text-2xl font-semibold tabular-nums">{c.value}</div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Control coverage by framework</CardTitle>
          </CardHeader>
          <CardContent>
            {coverage.length === 0 ? (
              <Skeleton className="h-[240px] w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={coverage} margin={{ left: -16 }}>
                  <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={12} />
                  <YAxis domain={[0, 100]} tickLine={false} axisLine={false} fontSize={12} />
                  <Bar dataKey="coverage" radius={[4, 4, 0, 0]} fill="var(--color-primary)" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
