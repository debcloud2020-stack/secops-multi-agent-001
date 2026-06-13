"""Graph state and domain models.

Some fields (``similar_past``, ``guardrail_flags``, ``cost``) are declared now but are
no-ops in Phase 1 — they belong to later phases (RAG memory, guardrail, cost tracking).
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

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

# Deterministic fallback order — guarantees all five agents are visited in Phase 1.
AGENT_ORDER: list[AgentName] = [
    "log_monitor",
    "threat_intel",
    "vuln_scanner",
    "policy_checker",
    "incident_response",
]


class CVEMatch(BaseModel):
    """A matched CVE with optional scores (mock values in Phase 1)."""

    cve_id: str
    summary: str = ""
    cvss: float | None = None
    epss: float | None = None
    kev: bool = False


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


class SecOpsState(BaseModel):
    """LangGraph state passed between the supervisor and agent nodes."""

    messages: Annotated[list, add_messages] = Field(default_factory=list)
    incident: Incident = Field(default_factory=Incident)
    findings: Annotated[list[Finding], operator.add] = Field(default_factory=list)

    # Routing / control
    next_agent: RouteTarget | None = None
    visited: Annotated[list[str], operator.add] = Field(default_factory=list)
    step: int = 0
    response_plan: str | None = None

    # Declared for later phases — unused / no-op in Phase 1.
    similar_past: list[dict] = Field(default_factory=list)
    guardrail_flags: list[str] = Field(default_factory=list)
    cost: dict = Field(default_factory=dict)
