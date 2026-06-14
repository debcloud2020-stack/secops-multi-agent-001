"""Graph state and domain models."""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


def merge_cost(left: dict, right: dict) -> dict:
    """Reducer that merges per-node cost dicts and keeps a running ``total``.

    Each node contributes ``{"per_agent": {name: tokens}, "total": tokens}``; the
    reducer sums overlapping agents and totals so concurrent/looping nodes accumulate.
    """
    out: dict = {"per_agent": dict(left.get("per_agent", {})), "total": left.get("total", 0)}
    for name, tokens in right.get("per_agent", {}).items():
        out["per_agent"][name] = out["per_agent"].get(name, 0) + tokens
    out["total"] = out.get("total", 0) + right.get("total", 0)
    return out

# Agent identifiers + the terminal sentinel, reused for routing and the visit order.
AgentName = Literal[
    "log_monitor",
    "threat_intel",
    "vuln_scanner",
    "policy_checker",
    "incident_response",
]
RouteTarget = Literal[
    "log_monitor",
    "threat_intel",
    "vuln_scanner",
    "policy_checker",
    "incident_response",
    "FINISH",
]

# Per-run data source selector (Phase 5b-1), shared by state + API schemas.
DataMode = Literal["mock", "live", "synthetic"]

# Deterministic fallback order — guarantees all five agents are visited in Phase 1.
AGENT_ORDER: list[AgentName] = [
    "log_monitor",
    "threat_intel",
    "vuln_scanner",
    "policy_checker",
    "incident_response",
]


class CVEMatch(BaseModel):
    """A matched CVE with enrichment scores and a computed priority."""

    cve_id: str
    summary: str = ""
    cvss: float | None = None
    epss: float | None = None
    in_kev: bool = False
    known_ransomware: bool = False
    priority: float = 0.0


class Finding(BaseModel):
    """A single observation produced by an agent."""

    agent: str
    title: str
    detail: str = ""
    severity: Literal["info", "low", "medium", "high", "critical"] = "info"
    cves: list[CVEMatch] = Field(default_factory=list)


class Incident(BaseModel):
    """The incident under investigation."""

    id: str = "INC-0001"
    title: str = ""
    description: str = ""
    severity: Literal["info", "low", "medium", "high", "critical"] = "high"
    source: str = "mock"
    # When true, incident_response pauses for human approval (HITL). Default false so the
    # CLI and tests run straight through; curated API incidents opt in explicitly.
    requires_approval: bool = False


class SecOpsState(BaseModel):
    """LangGraph state passed between the supervisor and agent nodes."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    incident: Incident = Field(default_factory=Incident)
    findings: Annotated[list[Finding], operator.add] = Field(default_factory=list)
    # First-class CVE table (PLAN.md §5/§9/§10), separate from per-finding context.
    cve_matches: Annotated[list[CVEMatch], operator.add] = Field(default_factory=list)

    # Per-run data source (mock fixtures / live Azure / synthetic custom table). Threaded
    # from the API into the tools; persisted in state so history/replay shows the mode.
    data_mode: DataMode = "mock"
    # Notices surfaced when a live/synthetic source was unavailable and the run fell back to mock.
    data_notices: Annotated[list[str], operator.add] = Field(default_factory=list)
    # Compact summary of the log_monitor source rows (additive; single writer, no reducer).
    source_rows: dict | None = None

    # Routing / control
    next_agent: RouteTarget | None = None
    visited: Annotated[list[str], operator.add] = Field(default_factory=list)
    step: int = 0
    response_plan: str | None = None

    # Feature layers (Phase 2).
    similar_past: list[dict] = Field(default_factory=list)
    guardrail_flags: Annotated[list[str], operator.add] = Field(default_factory=list)
    cost: Annotated[dict, merge_cost] = Field(default_factory=dict)

    # HITL (Phase 3): the approval decision once a paused run is resumed.
    approval: dict | None = None
