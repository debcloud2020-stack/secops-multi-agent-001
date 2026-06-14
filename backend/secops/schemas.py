"""API request/response models (PLAN.md §10)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from secops.state import CVEMatch, DataMode, Finding

RunStatusValue = Literal["queued", "running", "awaiting_approval", "completed", "rejected", "error"]


class RunRequest(BaseModel):
    incident_id: str
    data_mode: DataMode = "mock"


class ApproveRequest(BaseModel):
    decision: Literal["approve", "reject"]
    edited_plan: str | None = None


class RunCreated(BaseModel):
    run_id: str


class IncidentOut(BaseModel):
    id: str
    title: str
    description: str = ""
    severity: str = "high"
    requires_approval: bool = False


class RunStatus(BaseModel):
    run_id: str
    status: RunStatusValue
    incident_id: str
    data_mode: str = "mock"
    data_notices: list[str] = Field(default_factory=list)
    source_rows: dict | None = None
    visited: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    cve_matches: list[CVEMatch] = Field(default_factory=list)
    cost: dict = Field(default_factory=dict)
    guardrail_flags: list[str] = Field(default_factory=list)
    similar_past: list[dict] = Field(default_factory=list)
    plan: str | None = None
    error: str | None = None


class RunSummary(BaseModel):
    run_id: str
    incident_id: str
    status: RunStatusValue
    created: str


class Control(BaseModel):
    id: str
    name: str
    status: str


class Framework(BaseModel):
    name: str
    coverage_pct: float
    controls: list[Control] = Field(default_factory=list)


class ComplianceOut(BaseModel):
    frameworks: list[Framework] = Field(default_factory=list)
