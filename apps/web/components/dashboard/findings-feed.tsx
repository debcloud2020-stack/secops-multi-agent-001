import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SEVERITY_CLASS } from "@/lib/format";
import { summarizeFinding } from "@/lib/plan";
import { AGENT_LABELS, type Finding, type Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

// Pulsing status dot per severity — the "live" texture of the glass threat feed.
// text + bg share the accent so the glow (shadow uses currentColor) matches the dot.
const DOT_CLASS: Record<Severity, string> = {
  critical: "bg-red-400 text-red-400",
  high: "bg-orange-400 text-orange-400",
  medium: "bg-amber-400 text-amber-400",
  low: "bg-cyan-400 text-cyan-400",
  info: "bg-slate-400 text-slate-400",
};

export function FindingsFeed({ findings }: { findings: Finding[] }) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Threat feed ({findings.length})</CardTitle>
      </CardHeader>
      <CardContent className="flex-1">
        {findings.length === 0 ? (
          <p className="text-sm text-muted-foreground">No findings yet.</p>
        ) : (
          <ScrollArea className="h-[320px] pr-3">
            <ul className="space-y-2.5">
              {findings.map((f, i) => (
                <li
                  key={`${f.agent}-${i}`}
                  className="rounded-xl border border-white/10 bg-white/[0.03] p-3 transition-colors duration-200 hover:border-white/20 hover:bg-white/[0.06]"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                      <span
                        className={cn(
                          "size-2 shrink-0 animate-pulse rounded-full shadow-[0_0_8px_currentColor]",
                          DOT_CLASS[f.severity],
                        )}
                      />
                      {AGENT_LABELS[f.agent] ?? f.agent}
                    </span>
                    <Badge variant="outline" className={cn("text-xs", SEVERITY_CLASS[f.severity])}>
                      {f.severity}
                    </Badge>
                  </div>
                  <h4 className="mt-1.5 text-sm font-medium">{f.title}</h4>
                  {f.detail && (
                    <p className="mt-1 text-sm text-muted-foreground">
                      {summarizeFinding(f.agent, f.detail)}
                    </p>
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
