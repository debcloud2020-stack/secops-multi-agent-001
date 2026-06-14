// TypeScript mirrors of the Phase 3 API schemas (backend/secops/schemas.py).

export type RunStatusValue =
  | "queued"
  | "running"
  | "awaiting_approval"
  | "completed"
  | "rejected"
  | "error";

export type Severity = "info" | "low" | "medium" | "high" | "critical";

export interface CVEMatch {
  cve_id: string;
  summary: string;
  cvss: number | null;
  epss: number | null;
  in_kev: boolean;
  known_ransomware: boolean;
  priority: number;
}

export interface Finding {
  agent: string;
  title: string;
  detail: string;
  severity: Severity;
  cves: CVEMatch[];
}

export interface IncidentOut {
  id: string;
  title: string;
  description: string;
  severity: string;
  requires_approval: boolean;
}

export interface Cost {
  per_agent?: Record<string, number>;
  total?: number;
}

export interface SimilarIncident {
  id?: string;
  title?: string;
  summary?: string;
  plan?: string;
  created?: string;
  score?: number;
}

export interface SourceRows {
  kind: "operations" | "incidents" | "signins" | "empty" | string;
  source: string;
  count: number;
  operations?: { name: string; count: number }[];
  callers?: string[];
  source_ips?: string[];
  incidents?: { id: string; title: string; detection: string; severity: string }[];
  signins?: { user: string; ip: string; result: string; failures: number }[];
}

export interface RunStatus {
  run_id: string;
  status: RunStatusValue;
  incident_id: string;
  data_mode: string;
  data_notices: string[];
  source_rows?: SourceRows | null;
  visited: string[];
  findings: Finding[];
  cve_matches: CVEMatch[];
  cost: Cost;
  guardrail_flags: string[];
  similar_past: SimilarIncident[];
  plan: string | null;
  error: string | null;
}

export interface RunSummary {
  run_id: string;
  incident_id: string;
  status: RunStatusValue;
  created: string;
}

export interface Control {
  id: string;
  name: string;
  status: string;
}

export interface Framework {
  name: string;
  coverage_pct: number;
  controls: Control[];
}

export interface ComplianceOut {
  frameworks: Framework[];
}

export type DataMode = "mock" | "live" | "synthetic";
export type Decision = "approve" | "reject";

// The five agents, in supervisor visit order (backend AGENT_ORDER).
export const AGENT_ORDER = [
  "log_monitor",
  "threat_intel",
  "vuln_scanner",
  "policy_checker",
  "incident_response",
] as const;

export const AGENT_LABELS: Record<string, string> = {
  log_monitor: "Log Monitor",
  threat_intel: "Threat Intel",
  vuln_scanner: "Vuln Scanner",
  policy_checker: "Policy Checker",
  incident_response: "Incident Response",
};

export const TERMINAL_STATUSES: RunStatusValue[] = ["completed", "rejected", "error"];
