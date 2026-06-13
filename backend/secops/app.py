"""CLI entrypoint.

    uv run python -m secops.app run --incident "Critical RCE in gateway"

Runs the full graph over the mock incident fixture and prints findings + response plan.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from secops.graph import build_graph
from secops.state import Incident, SecOpsState

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mock_incident.json"


def _load_incident(title: str | None) -> Incident:
    data = json.loads(FIXTURE.read_text())
    incident = Incident(**data)
    if title:
        incident.title = title
    return incident


def run(title: str | None) -> SecOpsState:
    """Execute the graph and return the final state."""
    graph = build_graph()
    initial = SecOpsState(incident=_load_incident(title))
    config = {"configurable": {"thread_id": "phase1"}}
    final = graph.invoke(initial, config=config)
    return SecOpsState.model_validate(final)


def _print(state: SecOpsState) -> None:
    print(f"\n=== Incident: {state.incident.title} ===")
    print(f"Agents visited ({len(state.visited)}): {' -> '.join(state.visited)}\n")
    print("--- Findings ---")
    for f in state.findings:
        cve = f" [{', '.join(c.cve_id for c in f.cves)}]" if f.cves else ""
        print(f"  [{f.severity:>8}] {f.agent}: {f.title}{cve}")
    print("\n--- Response Plan ---")
    print(state.response_plan or "(none)")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secops")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="Run the supervisor graph over the mock incident")
    run_p.add_argument("--incident", default=None, help="Incident title")
    args = parser.parse_args(argv)

    if args.command == "run":
        _print(run(args.incident))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
