"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { CveTable } from "@/components/dashboard/cve-table";
import { PageHeader } from "@/components/dashboard/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getThreats } from "@/lib/api";
import type { CVEMatch } from "@/lib/types";

export default function ThreatsPage() {
  const [rows, setRows] = useState<CVEMatch[] | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    getThreats()
      .then(setRows)
      .catch(() => toast.error("Failed to load threats"));
  }, []);

  const filtered = useMemo(() => {
    if (!rows) return [];
    const needle = q.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter(
      (r) => r.cve_id.toLowerCase().includes(needle) || r.summary.toLowerCase().includes(needle),
    );
  }, [rows, q]);

  return (
    <>
      <PageHeader
        title="Threats"
        description="Priority-scored CVEs (CVSS · EPSS · KEV · ransomware) aggregated across runs."
      />
      <div className="space-y-4 p-6">
        <Input
          placeholder="Filter by CVE id or summary…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="max-w-sm"
        />
        <Card>
          <CardContent className="pt-2">
            {rows === null ? <Skeleton className="h-40 w-full" /> : <CveTable rows={filtered} />}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
