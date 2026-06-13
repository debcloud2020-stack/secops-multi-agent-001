import {
  ArrowRight,
  BrainCircuit,
  DatabaseZap,
  Code2,
  FileSearch,
  GaugeCircle,
  ListChecks,
  Network,
  Radar,
  ShieldAlert,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const AGENTS = [
  { icon: FileSearch, name: "Log Monitor", desc: "Curated KQL detections over Azure Sentinel sign-in and audit logs." },
  { icon: Radar, name: "Threat Intel", desc: "NVD + CISA KEV + EPSS enrichment into a single priority score." },
  { icon: DatabaseZap, name: "Vuln Scanner", desc: "trivy & pip-audit results, normalized and correlated to CVEs." },
  { icon: ListChecks, name: "Policy Checker", desc: "Agentic RAG over NIST CSF / ISO 27001 / SOC 2 controls." },
  { icon: ShieldCheck, name: "Incident Response", desc: "Synthesizes a response plan — with human-in-the-loop approval." },
];

const FEATURES = [
  { icon: Network, label: "Azure-native", desc: "Sentinel / Monitor via managed identity." },
  { icon: BrainCircuit, label: "Agentic RAG", desc: "LlamaIndex + LanceDB, local embeddings." },
  { icon: GaugeCircle, label: "Cost-aware", desc: "Two-tier models + per-run token panel." },
  { icon: ShieldAlert, label: "Injection-safe", desc: "Prompt-injection guardrail on ingested logs." },
  { icon: Workflow, label: "Eval-gated", desc: "Deterministic + LLM-judge eval harness." },
];

export default function LandingPage() {
  return (
    <main className="flex-1">
      {/* Hero */}
      <section className="relative overflow-hidden border-b">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(60%_50%_at_50%_0%,color-mix(in_oklch,var(--color-primary)_18%,transparent),transparent)]"
        />
        <div className="mx-auto max-w-5xl px-6 py-24 text-center sm:py-32">
          <Badge variant="secondary" className="mb-6 gap-1.5">
            <ShieldCheck className="size-3.5" />
            Multi-agent SOC, orchestrated with LangGraph
          </Badge>
          <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-6xl">
            Five security agents. <span className="text-primary">One supervisor.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg text-muted-foreground">
            SecOps triages an incident end-to-end — log analysis, threat intel, vulnerability
            scanning, compliance, and an approved response plan — grounded by agentic RAG and
            guarded against prompt injection.
          </p>
          <div className="mt-10 flex items-center justify-center gap-3">
            <Link href="/dashboard" className={cn(buttonVariants({ size: "lg" }))}>
              Open dashboard <ArrowRight className="size-4" />
            </Link>
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
            >
              <Code2 className="size-4" /> Source
            </a>
          </div>
        </div>
      </section>

      {/* How it works — five agents */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">How it works</h2>
          <p className="mt-3 text-muted-foreground">
            A cheap supervisor routes the incident through five specialists, then a strong model
            drafts the response plan.
          </p>
        </div>
        <ol className="grid gap-4 md:grid-cols-5">
          {AGENTS.map((a, i) => (
            <li
              key={a.name}
              className="relative rounded-xl border bg-card p-5 transition-colors hover:border-primary/40"
            >
              <span className="mb-3 inline-flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <a.icon className="size-5" />
              </span>
              <div className="text-xs font-medium text-muted-foreground">Step {i + 1}</div>
              <h3 className="mt-0.5 font-medium">{a.name}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{a.desc}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Architecture strip */}
      <section className="border-y bg-muted/30">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <h2 className="text-center text-2xl font-semibold tracking-tight">
            A checkpointed, auditable graph
          </h2>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-3 gap-y-2 font-mono text-sm">
            {["memory recall", "guardrail", "supervisor", "5 agents", "memory write"].map(
              (node, i, arr) => (
                <span key={node} className="flex items-center gap-3">
                  <span className="rounded-md border bg-background px-3 py-1.5">{node}</span>
                  {i < arr.length - 1 && <ArrowRight className="size-4 text-muted-foreground" />}
                </span>
              ),
            )}
          </div>
          <p className="mx-auto mt-6 max-w-2xl text-center text-sm text-muted-foreground">
            Untrusted log text passes through the guardrail before it ever reaches the model.
            Similar past incidents are recalled at the start and the run is persisted at the end.
          </p>
        </div>
      </section>

      {/* Feature strip */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {FEATURES.map((f) => (
            <div key={f.label} className="rounded-xl border bg-card p-5">
              <f.icon className="size-5 text-primary" />
              <h3 className="mt-3 font-medium">{f.label}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{f.desc}</p>
            </div>
          ))}
        </div>
        <div className="mt-14 flex flex-col items-center gap-4 rounded-2xl border bg-card p-10 text-center">
          <h2 className="text-2xl font-semibold tracking-tight">See it run</h2>
          <p className="max-w-xl text-muted-foreground">
            Pick a curated incident and watch the agent rail light up in real time, then approve
            the incident-response plan.
          </p>
          <Link href="/dashboard" className={cn(buttonVariants({ size: "lg" }))}>
            Open dashboard <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t">
        <div className="mx-auto max-w-6xl px-6 py-8 text-center text-sm text-muted-foreground">
          SecOps Multi-Agent — demo build. Not for production use.
        </div>
      </footer>
    </main>
  );
}
