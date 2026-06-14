import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MODE_ACCENT, SEVERITY_CLASS } from "@/lib/format";
import type { DataMode, Severity, SourceRows } from "@/lib/types";
import { cn } from "@/lib/utils";

/** A muted two-column header row above a source-rows list. */
function ColHeader({ left, right }: { left: string; right: string }) {
  return (
    <div className="flex items-center justify-between gap-3 pb-1 text-xs font-medium text-muted-foreground">
      <span>{left}</span>
      <span>{right}</span>
    </div>
  );
}

/** The real log rows behind a run — makes mock / live / synthetic visibly differ. */
export function SourceRowsPanel({ data, mode }: { data: SourceRows; mode?: DataMode }) {
  let body: React.ReactNode;

  if (data.kind === "operations") {
    body = (
      <div className="space-y-3">
        <ColHeader left="Operation" right="Events" />
        <ul className="divide-y text-sm">
          {(data.operations ?? []).map((o) => (
            <li key={o.name} className="flex items-center justify-between gap-3 py-1.5">
              <span className="truncate font-mono text-xs">{o.name}</span>
              <span className="shrink-0 tabular-nums text-muted-foreground">{o.count} events</span>
            </li>
          ))}
        </ul>
        {((data.callers?.length ?? 0) > 0 || (data.source_ips?.length ?? 0) > 0) && (
          <p className="text-xs text-muted-foreground">
            {data.callers?.length ? <>Callers: {data.callers.join(", ")}</> : null}
            {data.callers?.length && data.source_ips?.length ? " · " : null}
            {data.source_ips?.length ? <>IPs: {data.source_ips.join(", ")}</> : null}
          </p>
        )}
      </div>
    );
  } else if (data.kind === "incidents") {
    body = (
      <div className="space-y-3">
        <ColHeader left="Incident" right="Detection · Severity" />
        <ul className="divide-y text-sm">
          {(data.incidents ?? []).map((i) => (
            <li key={i.id} className="flex items-center justify-between gap-3 py-1.5">
              <div className="min-w-0">
                <span className="font-mono text-xs text-muted-foreground">{i.id}</span>
                <p className="truncate">{i.title}</p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span className="text-xs text-muted-foreground">{i.detection}</span>
                <Badge
                  variant="outline"
                  className={cn("capitalize", SEVERITY_CLASS[i.severity as Severity] ?? SEVERITY_CLASS.info)}
                >
                  {i.severity}
                </Badge>
              </div>
            </li>
          ))}
        </ul>
      </div>
    );
  } else if (data.kind === "signins") {
    body = (
      <div className="space-y-3">
        <ColHeader left="User · IP" right="Result · Failures" />
        <ul className="divide-y text-sm">
          {(data.signins ?? []).map((s, idx) => (
            <li key={`${s.user}-${idx}`} className="flex items-center justify-between gap-3 py-1.5">
              <div className="min-w-0">
                <p className="truncate">{s.user}</p>
                <span className="font-mono text-xs text-muted-foreground">{s.ip}</span>
              </div>
              <div className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
                <span className="max-w-[16rem] truncate">{s.result}</span>
                {s.failures > 0 && <span className="tabular-nums">{s.failures} fail</span>}
              </div>
            </li>
          ))}
        </ul>
      </div>
    );
  } else if (data.kind === "empty") {
    body = <p className="text-sm text-muted-foreground">No rows returned from {data.source}.</p>;
  } else {
    return null; // unrecognized kind → render nothing
  }

  return (
    <Card className={cn("border-l-2", mode && MODE_ACCENT[mode].border)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">
          Source rows
          <span className="ml-2 text-sm font-normal text-muted-foreground">
            {data.source} · {data.count} {data.count === 1 ? "row" : "rows"}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>{body}</CardContent>
    </Card>
  );
}
