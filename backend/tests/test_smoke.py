"""Phase 1 smoke test: all five agents visited + a response plan produced (offline)."""

from __future__ import annotations

from secops.app import run
from secops.llm import OfflineChatModel, get_llm_cheap, get_llm_strong
from secops.state import AGENT_ORDER


def test_offline_stub_selected_by_default():
    # mock_mode defaults to true -> both tiers use the offline stub.
    assert isinstance(get_llm_cheap(), OfflineChatModel)
    assert isinstance(get_llm_strong(), OfflineChatModel)


def test_full_graph_visits_all_agents_and_produces_plan():
    state = run("Critical RCE in gateway")

    # All five agents visited, in deterministic order.
    assert state.visited == AGENT_ORDER

    # A non-empty response plan was synthesized.
    assert state.response_plan
    assert "Response plan" in state.response_plan

    # One finding per agent (incident_response also adds its plan finding).
    agents_with_findings = {f.agent for f in state.findings}
    assert set(AGENT_ORDER).issubset(agents_with_findings)
