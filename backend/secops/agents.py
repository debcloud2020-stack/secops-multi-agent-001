"""Supervisor router, feature-layer nodes (memory/guardrail), and five agent nodes.

Each agent calls its real (mock-defaulted) tool and routes the untrusted tool output
through the guardrail before reasoning. Threat-intel and vuln-scanner populate the
first-class ``cve_matches`` table; every node records token cost. The supervisor consults
the cheap LLM for a triage note but routing stays deterministic (walks ``AGENT_ORDER``).
"""

from __future__ import annotations

from datetime import UTC, datetime

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

from secops import guardrail
from secops.config import get_settings
from secops.cost import cost_update
from secops.llm import get_llm_cheap, get_llm_strong
from secops.memory import memory_recall, memory_write
from secops.rag.index import knowledge_search
from secops.state import AGENT_ORDER, Finding, SecOpsState
from secops.tools import azure_logs, scanner
from secops.tools.threat_intel import enrich_cve, to_cve_match

_PRIMARY_CVE = "CVE-2026-00000"  # mock fixture CVE (kept for offline determinism)
# Real, well-known CVE used in non-mock modes so NVD/KEV/EPSS return real data
# (Log4Shell — present in NVD + CISA KEV + has an EPSS score).
_PRIMARY_CVE_LIVE = "CVE-2021-44228"

# The response steps that require human sign-off before execution (HITL).
_PROPOSED_STEPS = [
    "Isolate the affected gateway host from the network.",
    "Rotate credentials and revoke active sessions for the host.",
    "Apply the vendor patch for the identified RCE (KEV-listed).",
    "Hunt for lateral movement using the threat-intel indicators.",
    "File policy-exception remediation for the SLA/segmentation breaches.",
]


# --- Feature-layer nodes (run outside the supervisor loop) ---------------------------

def memory_recall_node(state: SecOpsState) -> dict:
    """Read similar past incidents at the start of a run."""
    hits = memory_recall(state.incident)
    msg = f"memory: recalled {len(hits)} similar past incident(s)"
    return {"similar_past": hits, "messages": [AIMessage(content=msg)]}


def guardrail_node(state: SecOpsState) -> dict:
    """Scan the incident text for injection before any agent reasons over it."""
    text = f"{state.incident.title}. {state.incident.description}"
    _safe, flags = guardrail.scan(text)
    msg = f"guardrail: {len(flags)} flag(s) on incident text"
    return {"guardrail_flags": flags, "messages": [AIMessage(content=msg)]}


def memory_write_node(state: SecOpsState) -> dict:
    """Persist the completed run to long-term memory at the end."""
    memory_write(state, created=datetime.now(UTC).isoformat())
    return {"messages": [AIMessage(content="memory: run persisted")]}


# --- Supervisor + routing ------------------------------------------------------------

def supervisor(state: SecOpsState) -> dict:
    """Pick the next agent deterministically; stop when all are visited or capped."""
    settings = get_settings()
    step = state.step + 1

    messages: list = []
    cost: dict = {}
    if step == 1:
        note = get_llm_cheap().invoke(
            f"Triage this security incident in one line: {state.incident.title}"
        )
        messages = [AIMessage(content=f"supervisor triage: {note.content}")]
        cost = cost_update("supervisor", state.incident.title, str(note.content))

    if step > settings.max_supervisor_steps:
        return {"step": step, "next_agent": "FINISH", "messages": messages, "cost": cost}

    nxt = next((a for a in AGENT_ORDER if a not in state.visited), None)
    target = nxt if nxt is not None else "FINISH"
    return {"step": step, "next_agent": target, "messages": messages, "cost": cost}


def route(state: SecOpsState) -> str:
    """Conditional-edge selector — returns the supervisor's chosen target."""
    return state.next_agent or "FINISH"


# --- Agent nodes (real, mock-defaulted tools through the guardrail) -------------------

def _source_rows(rows: list[dict]) -> dict:
    """Compact, JSON-safe summary of the log rows for the dashboard (additive surface only).

    Shape-driven so it stays correct even when live/synthetic fall back to a mock fixture:
    AzureActivity → ``operations``; the synthetic table → ``incidents``; sign-in rows → ``signins``.
    ``operations[].count`` is the **summed AzureActivity EventCount** per operation (the panel
    labels the column "Events"). Lists are capped to stay small.
    """
    total = len(rows)
    if not rows:
        return {"kind": "empty", "source": "AzureActivity", "count": 0}
    keys = rows[0].keys()

    if "OperationNameValue" in keys:  # live AzureActivity (or its mock fixture)
        events: dict[str, int] = {}
        for r in rows:
            op = str(r.get("OperationNameValue", ""))
            events[op] = events.get(op, 0) + int(r.get("EventCount") or 0)
        top = sorted(events.items(), key=lambda kv: kv[1], reverse=True)[:5]
        callers = list(dict.fromkeys(r.get("Caller") for r in rows if r.get("Caller")))[:3]
        ips = list(
            dict.fromkeys(r.get("CallerIpAddress") for r in rows if r.get("CallerIpAddress"))
        )[:3]
        return {
            "kind": "operations", "source": "AzureActivity", "count": total,
            "operations": [{"name": n, "count": c} for n, c in top],
            "callers": callers, "source_ips": ips,
        }

    if "IncidentId" in keys or "DetectionName" in keys:  # synthetic SecOpsSynthetic_CL
        return {
            "kind": "incidents", "source": "SecOpsSynthetic_CL", "count": total,
            "incidents": [
                {
                    "id": str(r.get("IncidentId", "")),
                    "title": str(r.get("Title", "")),
                    "detection": str(r.get("DetectionName", "")),
                    "severity": str(r.get("Severity", "")),
                }
                for r in rows[:8]
            ],
        }

    # sign-in rows (mock fixture / sign-in fallback)
    return {
        "kind": "signins", "source": "SigninLogs", "count": total,
        "signins": [
            {
                "user": str(r.get("UserPrincipalName", "")),
                "ip": str(r.get("IPAddress", "")),
                "result": str(r.get("ResultDescription", ""))[:80],
                "failures": int(r.get("FailureCount") or 0),
            }
            for r in rows[:5]
        ],
    }


def log_monitor(state: SecOpsState) -> dict:
    notices: list[str] = []
    # Live mode queries AzureActivity (real + populated); mock/synthetic use the sign-in
    # detection name (synthetic ignores it and queries the seeded custom table).
    detection = "azure_activity" if state.data_mode == "live" else "failed_signins_burst"
    rows = azure_logs.run_detection(detection, state.data_mode, notices)
    safe, flags = guardrail.scan_obj(rows)  # reason over `safe`, never raw rows
    note = " Guardrail flagged injected content in a log row." if flags else ""
    finding = Finding(
        agent="log_monitor",
        title="Anomalous auth spike on gateway host",
        detail=(
            f"Reviewed {len(rows)} sign-in rows: failed-login burst then success from a "
            f"new ASN, plus a suspicious privileged grant.{note}"
        ),
        severity="high",
    )
    return {
        "findings": [finding],
        "visited": ["log_monitor"],
        "guardrail_flags": flags,
        "data_notices": notices,
        "source_rows": _source_rows(rows),
        "cost": cost_update("log_monitor", safe),
    }


def threat_intel(state: SecOpsState) -> dict:
    notices: list[str] = []
    cve = _PRIMARY_CVE if state.data_mode == "mock" else _PRIMARY_CVE_LIVE
    enrichment = enrich_cve(cve, state.data_mode, notices)
    match = to_cve_match(enrichment)
    safe_summary, flags = guardrail.scan(enrichment["summary"])
    kb = knowledge_search("remote code execution edge gateway advisory response", k=2)
    kb_hint = kb[0][:120].replace("\n", " ") if kb else "(no KB hit)"
    finding = Finding(
        agent="threat_intel",
        title=f"{match.cve_id} prioritized (score {match.priority})",
        detail=(
            f"CVSS {match.cvss}, EPSS {match.epss}, KEV={match.in_kev}, "
            f"ransomware={match.known_ransomware}. KB: {kb_hint}"
        ),
        severity="high",
        cves=[match],
    )
    return {
        "findings": [finding],
        "visited": ["threat_intel"],
        "cve_matches": [match],
        "guardrail_flags": flags,
        "data_notices": notices,
        "cost": cost_update("threat_intel", safe_summary, *kb),
    }


def vuln_scanner(state: SecOpsState) -> dict:
    notices: list[str] = []
    # Non-mock runs a real filesystem scan (trivy fs .); mock uses the image fixture.
    target = "fs" if state.data_mode != "mock" else "image"
    results = scanner.scan(target, state.data_mode, notices)
    matches = []
    for r in results:
        cid = r.get("id") or ""
        if cid.startswith("CVE-"):
            m = to_cve_match(enrich_cve(cid, state.data_mode, notices))
            if not m.summary:
                m.summary = f"{r['package']} {r['installed']} → fix {r['fixed']}"
            matches.append(m)
    top = max((m.priority for m in matches), default=0.0)
    finding = Finding(
        agent="vuln_scanner",
        title="Unpatched vulnerabilities on the gateway",
        detail=f"Scanner found {len(results)} vulns ({len(matches)} CVEs); top priority {top}.",
        severity="critical" if top >= 7 else "high",
        cves=matches,
    )
    return {
        "findings": [finding],
        "visited": ["vuln_scanner"],
        "cve_matches": matches,
        "data_notices": notices,
        "cost": cost_update("vuln_scanner", *[m.summary for m in matches]),
    }


def policy_checker(state: SecOpsState) -> dict:
    controls = knowledge_search("patch SLA segmentation privileged access control", k=3)
    cited = "; ".join(c.split("\n", 1)[0].lstrip("# ") for c in controls[:3]) or "(no controls)"
    finding = Finding(
        agent="policy_checker",
        title="Patch-SLA and segmentation policy violations",
        detail=f"Critical patch SLA breached; gateway not segmented. Controls: {cited}",
        severity="medium",
    )
    return {
        "findings": [finding],
        "visited": ["policy_checker"],
        "cost": cost_update("policy_checker", *controls),
    }


def incident_response(state: SecOpsState) -> dict:
    """Synthesize a response plan (STRONG tier + memory), pausing for HITL approval.

    When ``incident.requires_approval`` is set, ``interrupt`` pauses the run as the first
    action (nothing expensive runs before it, so resume re-execution repeats no work).
    A reject finishes the run without executing the proposed steps.
    """
    approval: dict = {"decision": "approve", "edited_plan": None}
    if state.incident.requires_approval:
        approval = interrupt(
            {
                "action": "approve_response_plan",
                "incident": state.incident.title,
                "proposed_steps": [f"[APPROVAL REQUIRED] {s}" for s in _PROPOSED_STEPS],
            }
        )

    if isinstance(approval, dict) and approval.get("decision") == "reject":
        plan = (
            f"Response plan for '{state.incident.title}': [REJECTED] — the proposed "
            "steps were not executed (rejected by a human reviewer)."
        )
        finding = Finding(
            agent="incident_response",
            title="Response plan rejected",
            detail=plan,
            severity="info",
        )
        return {
            "findings": [finding],
            "visited": ["incident_response"],
            "response_plan": plan,
            "approval": approval,
            "cost": cost_update("incident_response", plan),
        }

    summary = "; ".join(f"{f.agent}: {f.title}" for f in state.findings)
    prior = (
        f" Similar past incident: {state.similar_past[0]['title']}."
        if state.similar_past else ""
    )
    prompt = (
        "You are an incident-response lead. Given these findings, produce a concise "
        f"response plan.\nFindings: {summary}{prior}"
    )
    synthesis = get_llm_strong().invoke(prompt)
    edited = approval.get("edited_plan") if isinstance(approval, dict) else None
    plan = edited or (
        f"Response plan for '{state.incident.title}':\n"
        + "".join(f"{i}. {s}\n" for i, s in enumerate(_PROPOSED_STEPS, 1))
        + f"{('[memory] ' + state.similar_past[0]['title']) if state.similar_past else ''}\n"
        + f"[synthesis] {synthesis.content}"
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
        "approval": approval,
        "cost": cost_update("incident_response", prompt, str(synthesis.content)),
    }
