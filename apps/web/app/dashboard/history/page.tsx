"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

import { ModeBadge } from "@/components/dashboard/mode-badge";
import { PageHeader } from "@/components/dashboard/page-header";
import { RunResult } from "@/components/dashboard/run-result";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useRun } from "@/hooks/use-run";
import { listRuns } from "@/lib/api";
import type { DataMode, RunSummary } from "@/lib/types";

function HistoryInner() {
  const router = useRouter();
  const params = useSearchParams();
  const selectedId = params.get("run_id");
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const { run, load } = useRun();

  useEffect(() => {
    listRuns()
      .then(setRuns)
      .catch(() => toast.error("Failed to load history"));
  }, []);

  useEffect(() => {
    if (selectedId) void load(selectedId);
  }, [selectedId, load]);

  if (selectedId) {
    return (
      <>
        <PageHeader
          title="Run detail"
          description={`Replay of run ${selectedId.slice(0, 8)}`}
          actions={
            <Button variant="outline" size="sm" onClick={() => router.push("/dashboard/history")}>
              <ArrowLeft className="size-4" /> Back
            </Button>
          }
        />
        <div className="space-y-4 p-6">
          {run ? (
            <>
              <div className="flex items-center gap-3">
                {run.data_mode && <ModeBadge mode={run.data_mode as DataMode} />}
                <StatusBadge status={run.status} />
              </div>
              <RunResult run={run} mode={run.data_mode as DataMode} />
            </>
          ) : (
            <Skeleton className="h-80 w-full" />
          )}
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader title="History" description="Past runs. Select one to replay its result." />
      <div className="p-6">
        <Card>
          <CardContent className="pt-2">
            {runs === null ? (
              <Skeleton className="h-40 w-full" />
            ) : runs.length === 0 ? (
              <p className="py-6 text-sm text-muted-foreground">No runs yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Run</TableHead>
                    <TableHead>Incident</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...runs].reverse().map((r) => (
                    <TableRow
                      key={r.run_id}
                      className="cursor-pointer"
                      onClick={() => router.push(`/dashboard/history?run_id=${r.run_id}`)}
                    >
                      <TableCell className="font-mono text-xs">{r.run_id.slice(0, 8)}</TableCell>
                      <TableCell>{r.incident_id}</TableCell>
                      <TableCell>
                        <StatusBadge status={r.status} />
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {r.created?.slice(0, 19).replace("T", " ")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

export default function HistoryPage() {
  return (
    <Suspense fallback={<div className="p-6"><Skeleton className="h-80 w-full" /></div>}>
      <HistoryInner />
    </Suspense>
  );
}
