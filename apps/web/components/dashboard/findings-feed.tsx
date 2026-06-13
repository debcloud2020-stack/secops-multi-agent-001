import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SEVERITY_CLASS } from "@/lib/format";
import { AGENT_LABELS, type Finding } from "@/lib/types";
import { cn } from "@/lib/utils";

export function FindingsFeed({ findings }: { findings: Finding[] }) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Findings ({findings.length})</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        {findings.length === 0 ? (
          <p className="text-sm text-muted-foreground">No findings yet.</p>
        ) : (
          <ScrollArea className="h-[320px] pr-3">
            <ul className="space-y-3">
              {findings.map((f, i) => (
                <li key={`${f.agent}-${i}`} className="rounded-lg border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-muted-foreground">
                      {AGENT_LABELS[f.agent] ?? f.agent}
                    </span>
                    <Badge variant="outline" className={cn("text-xs", SEVERITY_CLASS[f.severity])}>
                      {f.severity}
                    </Badge>
                  </div>
                  <h4 className="mt-1 text-sm font-medium">{f.title}</h4>
                  {f.detail && (
                    <p className="mt-1 text-sm text-muted-foreground">{f.detail}</p>
                  )}
                </li>
              ))}
            </ul>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
