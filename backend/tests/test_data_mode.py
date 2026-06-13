"""Per-run data_mode (Phase 5b-1): live/synthetic fall back to mock with a notice."""

from __future__ import annotations

from secops.graph import build_graph
from secops.state import AGENT_ORDER, Incident, SecOpsState
from secops.tools import azure_logs


def test_live_tool_falls_back_to_mock_with_notice():
    """With no Azure creds, a 'live' detection returns mock rows and records a notice."""
    notices: list[str] = []
    rows = azure_logs.run_detection("failed_signins_burst", "live", notices)
    assert rows  # got the mock fixture rows
    assert any("log_monitor" in n for n in notices)


def test_synthetic_tool_falls_back_to_mock_with_notice():
    notices: list[str] = []
    rows = azure_logs.run_detection("failed_signins_burst", "synthetic", notices)
    assert rows
    assert any("synthetic" in n for n in notices)


def test_graph_live_completes_and_surfaces_notices(tmp_lancedb, embed_available):
    """A full 'live' run with no creds still visits all agents and reports fell-back notices."""
    graph = build_graph()
    final = graph.invoke(
        SecOpsState(incident=Incident(title="RCE", description="x"), data_mode="live"),
        {"configurable": {"thread_id": "dm-live"}},
    )
    state = SecOpsState.model_validate(final)
    assert state.visited == AGENT_ORDER
    assert state.data_mode == "live"
    assert state.data_notices  # at least the log_monitor fallback


def test_graph_mock_has_no_notices(tmp_lancedb, embed_available):
    graph = build_graph()
    final = graph.invoke(
        SecOpsState(incident=Incident(title="RCE", description="x")),
        {"configurable": {"thread_id": "dm-mock"}},
    )
    state = SecOpsState.model_validate(final)
    assert state.data_mode == "mock"
    assert state.data_notices == []
