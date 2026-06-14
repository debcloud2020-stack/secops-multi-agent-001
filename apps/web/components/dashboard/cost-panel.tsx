import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AGENT_LABELS, type Cost } from "@/lib/types";

export function CostPanel({ cost }: { cost: Cost }) {
  const perAgent = cost.per_agent ?? {};
  const total = cost.total ?? 0;
  const max = Math.max(1, ...Object.values(perAgent));
  const entries = Object.entries(perAgent);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          Cost
          <span className="font-mono text-sm font-normal tabular-nums text-cyan-300">
            {total} tok
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No token usage yet.</p>
        ) : (
          <ul className="space-y-2">
            {entries.map(([node, tokens]) => (
              <li key={node} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span>{AGENT_LABELS[node] ?? node}</span>
                  <span className="tabular-nums text-muted-foreground">{tokens}</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-emerald-400"
                    style={{ width: `${(tokens / max) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
