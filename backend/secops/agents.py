"""Supervisor router + five agent nodes (mock findings) + conditional-edge routing.

Phase 1 is mock-only: agents return canned ``Finding`` objects (no real tools). The
supervisor consults the cheap LLM for a triage note but routing is **deterministic** —
it walks ``AGENT_ORDER`` and visits each unvisited agent once — so the graph reliably
visits all five agents. ``max_supervisor_steps`` is a hard loop guard.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from secops.config import get_settings
from secops.llm import get_llm_cheap, get_llm_strong
from secops.state import (
    AGENT_ORDER,
    CVEMatch,
    Finding,
    SecOpsState,
)


def supervisor(state: SecOpsState) -> dict:
    """Pick the next agent deterministically; stop when all are visited or capped."""
    settings = get_settings()
    step = state.step + 1

    # On the first step, consult the cheap model for a short triage note (demonstrates
    # the cheap tier; does not drive routing in Phase 1).
    messages: list = []
    if step == 1:
        note = get_llm_cheap().invoke(
            f"Triage this security incident in one line: {state.incident.title}"
        )
        messages = [AIMessage(content=f"supervisor triage: {note.content}")]

    if step > settings.max_supervisor_steps:
        return {"step": step, "next_agent": "FINISH", "messages": messages}

    nxt = next((a for a in AGENT_ORDER if a not in state.visited), None)
    target = nxt if nxt is not None else "FINISH"
    return {"step": step, "next_agent": target, "messages": messages}


def route(state: SecOpsState) -> str:
    """Conditional-edge selector — returns the supervisor's chosen target."""
    return state.next_agent or "FINISH"


def _finding(state: SecOpsState, **kwargs) -> dict:
    """Build the standard node return: one mock finding + mark the agent visited."""
    finding = Finding(**kwargs)
    return {"findings": [finding], "visited": [finding.agent]}


def log_monitor(state: SecOpsState) -> dict:
    return _finding(
        state,
        agent="log_monitor",
        title="Anomalous auth spike on gateway host",
        detail="Mock: 3x failed-login burst then a successful root login from a new ASN.",
        severity="high",
    )


def threat_intel(state: SecOpsState) -> dict:
    return _finding(
        state,
        agent="threat_intel",
        title="Source IP matches known exploit infrastructure",
        detail="Mock: indicator overlaps a tracked actor staging RCE payloads.",
        severity="high",
    )


def vuln_scanner(state: SecOpsState) -> dict:
    return _finding(
        state,
        agent="vuln_scanner",
        title="Unpatched RCE on the gateway",
        detail="Mock: vulnerable component version detected on the affected host.",
        severity="critical",
        cves=[
            CVEMatch(
                cve_id="CVE-2026-00000",
                summary="Mock unauthenticated RCE in edge gateway",
                cvss=9.8,
                epss=0.92,
                kev=True,
            )
        ],
    )


def policy_checker(state: SecOpsState) -> dict:
    return _finding(
        state,
        agent="policy_checker",
        title="Patch-SLA and segmentation policy violations",
        detail="Mock: critical patch SLA breached; gateway not isolated per policy.",
        severity="medium",
    )


def incident_response(state: SecOpsState) -> dict:
    """Synthesize a response plan using the STRONG model tier."""
    summary = "; ".join(f"{f.agent}: {f.title}" for f in state.findings)
    llm = get_llm_strong()
    synthesis = llm.invoke(
        "You are an incident-response lead. Given these findings, produce a concise "
        f"response plan.\nFindings: {summary}"
    )
    plan = (
        "Response plan for "
        f"'{state.incident.title}':\n"
        "1. Isolate the affected gateway host from the network.\n"
        "2. Rotate credentials and revoke active sessions for the host.\n"
        "3. Apply the vendor patch for the identified RCE (KEV-listed).\n"
        "4. Hunt for lateral movement using the threat-intel indicators.\n"
        "5. File policy-exception remediation for the SLA/segmentation breaches.\n"
        f"[synthesis] {synthesis.content}"
    )
    finding = Finding(
        agent="incident_response",
        title="Response plan generated",
        detail=plan,
        severity="info",
    )
    return {
        "findings": [finding],
        "visited": ["incident_response"],
        "response_plan": plan,
    }
