"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/dashboard/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getCompliance } from "@/lib/api";
import type { ComplianceOut } from "@/lib/types";
import { cn } from "@/lib/utils";

const STATUS_CLASS: Record<string, string> = {
  covered: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  partial: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  gap: "bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/30",
};

export default function CompliancePage() {
  const [data, setData] = useState<ComplianceOut | null>(null);

  useEffect(() => {
    getCompliance()
      .then(setData)
      .catch(() => toast.error("Failed to load compliance"));
  }, []);

  return (
    <>
      <PageHeader
        title="Compliance"
        description="Control coverage per framework (NIST CSF · ISO 27001 · SOC 2)."
      />
      <div className="p-6">
        {!data ? (
          <Skeleton className="h-80 w-full" />
        ) : (
          <Tabs defaultValue={data.frameworks[0]?.name}>
            <TabsList>
              {data.frameworks.map((f) => (
                <TabsTrigger key={f.name} value={f.name}>
                  {f.name}
                </TabsTrigger>
              ))}
            </TabsList>
            {data.frameworks.map((f) => (
              <TabsContent key={f.name} value={f.name} className="mt-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center justify-between text-base">
                      {f.name}
                      <span className="text-sm font-normal text-muted-foreground">
                        {f.coverage_pct}% covered
                      </span>
                    </CardTitle>
                    <Progress value={f.coverage_pct} className="mt-1" />
                  </CardHeader>
                  <CardContent>
                    <ul className="divide-y">
                      {f.controls.map((c) => (
                        <li key={c.id} className="flex items-center justify-between gap-3 py-2.5">
                          <div>
                            <span className="font-mono text-xs text-muted-foreground">{c.id}</span>
                            <p className="text-sm">{c.name}</p>
                          </div>
                          <Badge variant="outline" className={cn("capitalize", STATUS_CLASS[c.status])}>
                            {c.status}
                          </Badge>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </TabsContent>
            ))}
          </Tabs>
        )}
      </div>
    </>
  );
}
