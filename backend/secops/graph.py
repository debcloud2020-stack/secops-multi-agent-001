"""Assemble the LangGraph StateGraph.

START -> supervisor -> (conditional) each agent -> supervisor -> ... -> FINISH -> END.
Compiled with an in-memory checkpointer (MemorySaver).
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from secops.agents import (
    incident_response,
    log_monitor,
    policy_checker,
    route,
    supervisor,
    threat_intel,
    vuln_scanner,
)
from secops.state import AGENT_ORDER, SecOpsState

_NODES = {
    "log_monitor": log_monitor,
    "threat_intel": threat_intel,
    "vuln_scanner": vuln_scanner,
    "policy_checker": policy_checker,
    "incident_response": incident_response,
}


def build_graph():
    """Build and compile the SecOps supervisor graph."""
    builder = StateGraph(SecOpsState)

    builder.add_node("supervisor", supervisor)
    for name, fn in _NODES.items():
        builder.add_node(name, fn)

    builder.add_edge(START, "supervisor")

    # Supervisor routes to an agent by name, or to END on FINISH.
    path_map = {name: name for name in AGENT_ORDER}
    path_map["FINISH"] = END
    builder.add_conditional_edges("supervisor", route, path_map)

    # Every agent returns control to the supervisor.
    for name in _NODES:
        builder.add_edge(name, "supervisor")

    return builder.compile(checkpointer=MemorySaver())
