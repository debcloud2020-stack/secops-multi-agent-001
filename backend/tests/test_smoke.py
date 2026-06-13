"""Phase 2 smoke test: full graph end-to-end on mock data, with feature layers."""

from __future__ import annotations

from secops.app import run
from secops.llm import OfflineChatModel, get_llm_cheap, get_llm_strong
from secops.state import AGENT_ORDER


def test_offline_stub_selected_by_default():
    assert isinstance(get_llm_cheap(), OfflineChatModel)
    assert isinstance(get_llm_strong(), OfflineChatModel)


def test_full_graph_phase2(tmp_lancedb, embed_available):
    # First run: five agents, plan, guardrail catch on the injected log row, cost > 0.
    state = run("Critical RCE in gateway", thread_id="t1")

    assert state.visited == AGENT_ORDER
    assert state.response_plan and "Response plan" in state.response_plan

    agents_with_findings = {f.agent for f in state.findings}
    assert set(AGENT_ORDER).issubset(agents_with_findings)

    # CVE enrichment surfaced with the priority score.
    assert any(m.cve_id == "CVE-2026-00000" and m.priority == 8.7 for m in state.cve_matches)

    # A planted injected log line was flagged (not acted on).
    assert state.guardrail_flags

    # Cost was accumulated.
    assert state.cost.get("total", 0) > 0

    # Second, similar incident recalls the first from long-term memory.
    second = run("Remote code execution on the perimeter gateway", thread_id="t2")
    assert second.similar_past, "second similar incident should recall the first"
