"""Assemble the LangGraph StateGraph (Phase 2 flow).

START -> memory_recall -> guardrail -> supervisor ⇄ [five agents] -> (FINISH)
      -> memory_write -> END.   Compiled with an in-memory checkpointer (MemorySaver).
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from secops.agents import (
    guardrail_node,
    incident_response,
    log_monitor,
    memory_recall_node,
    memory_write_node,
    policy_checker,
    route,
    supervisor,
    threat_intel,
    vuln_scanner,
)
from secops.state import AGENT_ORDER, SecOpsState

_AGENTS = {
    "log_monitor": log_monitor,
    "threat_intel": threat_intel,
    "vuln_scanner": vuln_scanner,
    "policy_checker": policy_checker,
    "incident_response": incident_response,
}


def build_graph():
    """Build and compile the SecOps supervisor graph."""
    builder = StateGraph(SecOpsState)

    builder.add_node("memory_recall", memory_recall_node)
    builder.add_node("guardrail", guardrail_node)
    builder.add_node("memory_write", memory_write_node)
    builder.add_node("supervisor", supervisor)
    for name, fn in _AGENTS.items():
        builder.add_node(name, fn)

    # Pre-supervisor: read memory, then sanitize incident text.
    builder.add_edge(START, "memory_recall")
    builder.add_edge("memory_recall", "guardrail")
    builder.add_edge("guardrail", "supervisor")

    # Supervisor routes to an agent by name, or to memory_write on FINISH.
    path_map = {name: name for name in AGENT_ORDER}
    path_map["FINISH"] = "memory_write"
    builder.add_conditional_edges("supervisor", route, path_map)

    # Every agent returns control to the supervisor.
    for name in _AGENTS:
        builder.add_edge(name, "supervisor")

    # Persist the run, then end.
    builder.add_edge("memory_write", END)

    return builder.compile(checkpointer=MemorySaver())
