import { ShieldAlert, ShieldCheck } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function GuardrailFlags({ flags }: { flags: string[] }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          {flags.length > 0 ? (
            <ShieldAlert className="size-4 text-amber-400" />
          ) : (
            <ShieldCheck className="size-4 text-emerald-400" />
          )}
          Guardrail flags
        </CardTitle>
      </CardHeader>
      <CardContent>
        {flags.length === 0 ? (
          <p className="text-sm text-muted-foreground">No injection detected in ingested text.</p>
        ) : (
          <ul className="space-y-1.5">
            {flags.map((flag, i) => (
              <li
                key={i}
                className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1.5 font-mono text-xs text-amber-200"
              >
                <span className="size-2 shrink-0 animate-pulse rounded-full bg-amber-400 text-amber-400 shadow-[0_0_8px_currentColor]" />
                {flag}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
