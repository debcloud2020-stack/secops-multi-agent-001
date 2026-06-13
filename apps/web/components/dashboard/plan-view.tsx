import { ClipboardList } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function PlanView({ plan }: { plan: string | null }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ClipboardList className="size-4 text-primary" />
          Response plan
        </CardTitle>
      </CardHeader>
      <CardContent>
        {plan ? (
          <pre className="whitespace-pre-wrap rounded-lg bg-muted/50 p-4 text-sm leading-relaxed">
            {plan}
          </pre>
        ) : (
          <p className="text-sm text-muted-foreground">
            The incident-response plan appears here once the run completes.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
