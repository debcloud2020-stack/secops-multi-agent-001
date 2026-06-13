import { Clock } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SimilarIncident } from "@/lib/types";

export function SimilarIncidents({ items }: { items: SimilarIncident[] }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Similar past incidents</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">None recalled from memory.</p>
        ) : (
          <ul className="space-y-2">
            {items.map((s, i) => (
              <li key={s.id ?? i} className="rounded-lg border p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">{s.title ?? s.id ?? "Incident"}</span>
                  {typeof s.score === "number" && (
                    <span className="text-xs text-muted-foreground">score {s.score.toFixed(3)}</span>
                  )}
                </div>
                {s.created && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="size-3" /> {s.created}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
