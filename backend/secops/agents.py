"""Supervisor router, feature-layer nodes (memory/guardrail), and five agent nodes.

Each agent calls its real (mock-defaulted) tool and routes the untrusted tool output
through the guardrail before reasoning. Threat-intel and vuln-scanner populate the
first-class ``cve_matches`` table; every node records token cost. The supervisor consults
the cheap LLM for a triage note but routing stays deterministic (walks ``AGENT_ORDER``).
"""

from __future__ import annotations

from datetime import UTC, datetime

from langchain_core.messages import AIMessage

from secops import guardrail
from secops.config import get_settings
from secops.cost import cost_update
from secops.llm import get_llm_cheap, get_llm_strong
from secops.memory import memory_recall, memory_write
from secops.rag.index import knowledge_search
from secops.state import AGENT_ORDER, Finding, SecOpsState
from secops.tools import azure_logs, scanner
from secops.tools.threat_intel import enrich_cve, to_cve_match

_PRIMARY_CVE = "CVE-2026-00000"


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

def log_monitor(state: SecOpsState) -> dict:
    rows = azure_logs.run_detection("failed_signins_burst")
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
        "cost": cost_update("log_monitor", safe),
    }


def threat_intel(state: SecOpsState) -> dict:
    enrichment = enrich_cve(_PRIMARY_CVE)
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
        "cost": cost_update("threat_intel", safe_summary, *kb),
    }


def vuln_scanner(state: SecOpsState) -> dict:
    results = scanner.scan("image")
    matches = []
    for r in results:
        cid = r.get("id") or ""
        if cid.startswith("CVE-"):
            m = to_cve_match(enrich_cve(cid))
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
    """Synthesize a response plan using the STRONG model tier + recalled memory."""
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
    plan = (
        f"Response plan for '{state.incident.title}':\n"
        "1. Isolate the affected gateway host from the network.\n"
        "2. Rotate credentials and revoke active sessions for the host.\n"
        "3. Apply the vendor patch for the identified RCE (KEV-listed).\n"
        "4. Hunt for lateral movement using the threat-intel indicators.\n"
        "5. File policy-exception remediation for the SLA/segmentation breaches.\n"
        f"{('[memory] ' + state.similar_past[0]['title']) if state.similar_past else ''}\n"
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
        "cost": cost_update("incident_response", prompt, str(synthesis.content)),
    }
