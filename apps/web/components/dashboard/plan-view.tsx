import { ClipboardList } from "lucide-react";
import ReactMarkdown, { type Components } from "react-markdown";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { canonicalPlan } from "@/lib/plan";

// Dark/glass-friendly markdown elements with AA contrast on the navy background.
const MD: Components = {
  h1: (p) => <h3 className="font-heading text-base font-semibold text-foreground" {...p} />,
  h2: (p) => <h4 className="font-heading text-sm font-semibold text-foreground" {...p} />,
  h3: (p) => <h5 className="text-sm font-semibold text-foreground" {...p} />,
  p: (p) => <p className="text-sm leading-relaxed text-slate-300" {...p} />,
  ul: (p) => <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300 marker:text-cyan-400" {...p} />,
  ol: (p) => <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-300 marker:text-cyan-400" {...p} />,
  li: (p) => <li className="leading-relaxed" {...p} />,
  strong: (p) => <strong className="font-semibold text-foreground" {...p} />,
  em: (p) => <em className="italic text-slate-200" {...p} />,
  a: (p) => <a className="text-cyan-300 underline underline-offset-2" {...p} />,
  code: (p) => (
    <code className="rounded bg-white/10 px-1 py-0.5 font-mono text-xs text-cyan-200" {...p} />
  ),
};

export function PlanView({ plan }: { plan: string | null }) {
  const text = canonicalPlan(plan);
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ClipboardList className="size-4 text-cyan-400" />
          Response plan
        </CardTitle>
      </CardHeader>
      <CardContent>
        {text ? (
          <div className="space-y-2.5 rounded-xl border border-white/10 bg-white/[0.03] p-4">
            <ReactMarkdown components={MD}>{text}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            The incident-response plan appears here once the run completes.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
