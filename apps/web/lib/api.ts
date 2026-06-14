// Fetch wrapper for the API: reads the base URL from NEXT_PUBLIC_API_URL and surfaces a
// typed ApiError. The API is open — no auth header.

import type {
  ComplianceOut,
  CVEMatch,
  Decision,
  IncidentOut,
  RunStatus,
  RunSummary,
} from "@/lib/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

// --- Core request -------------------------------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    throw new ApiError(res.status, `${init?.method ?? "GET"} ${path} → ${res.status}`);
  }
  return (await res.json()) as T;
}

// --- Endpoints ----------------------------------------------------------------------

export const checkHealth = () => request<{ status: string }>("/health");
export const getIncidents = () => request<IncidentOut[]>("/incidents");
export const listRuns = () => request<RunSummary[]>("/runs");
export const getRun = (id: string) => request<RunStatus>(`/runs/${id}`);
export const getThreats = () => request<CVEMatch[]>("/threats");
export const getCompliance = () => request<ComplianceOut>("/compliance");

export const startRun = (incidentId: string, dataMode = "mock") =>
  request<{ run_id: string }>("/runs", {
    method: "POST",
    body: JSON.stringify({ incident_id: incidentId, data_mode: dataMode }),
  });

export const approveRun = (id: string, decision: Decision, editedPlan?: string | null) =>
  request<RunStatus>(`/runs/${id}/approve`, {
    method: "POST",
    body: JSON.stringify({ decision, edited_plan: editedPlan ?? null }),
  });
