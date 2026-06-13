"""Run the SecOps graph over the golden set (offline). Pure helpers, no assertions.

Reused by the pytest runner (``test_agents.py``), the baseline reporter
(``report_baseline.py``), and the optional LangSmith experiment (``experiment.py``).
The whole suite runs in **file order** on one compiled graph and one shared LanceDB so
the memory pair works: example A persists at END, then a later similar example B recalls
it via ``memory_recall``.
"""

from __future__ import annotations

import json
from typing import Any

from evals._bootstrap import GOLDEN_PATH


def load_golden(path: Any = None) -> list[dict]:
    """Load and parse ``datasets/golden.jsonl`` into a list of example dicts."""
    path = path or GOLDEN_PATH
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def run_example(graph: Any, example: dict, thread_id: str) -> Any:
    """Invoke the graph for one example; auto-approve a HITL pause when expected.

    Returns the validated final ``SecOpsState``.
    """
    from langgraph.types import Command

    from secops.state import Incident, SecOpsState

    cfg = {"configurable": {"thread_id": thread_id}}
    graph.invoke(SecOpsState(incident=Incident(**example["incident"])), config=cfg)

    snap = graph.get_state(cfg)
    if snap.interrupts and example.get("expect", {}).get("auto_approve"):
        graph.invoke(
            Command(resume={"decision": "approve", "edited_plan": None}), config=cfg
        )
        snap = graph.get_state(cfg)

    return SecOpsState.model_validate(snap.values)


def build_graph_and_index() -> Any:
    """Build the RAG index then a compiled graph (for the LangSmith experiment path)."""
    from secops.graph import build_graph
    from secops.rag.index import build_index

    build_index()
    return build_graph()


def run_suite(golden: list[dict], graph: Any = None) -> list[tuple[dict, Any]]:
    """Run every example in order on one shared graph; return ``[(example, state), …]``."""
    from secops.graph import build_graph

    graph = graph or build_graph()
    results: list[tuple[dict, Any]] = []
    for i, example in enumerate(golden):
        state = run_example(graph, example, thread_id=f"eval-{i}-{example['id']}")
        results.append((example, state))
    return results
