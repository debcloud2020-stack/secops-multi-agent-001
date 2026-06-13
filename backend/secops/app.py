"""CLI entrypoint.

    uv run python -m secops.app run --incident "<title>"   # run the graph over the mock incident
    uv run python -m secops.app index                       # (re)build the RAG knowledge index

Runs the full Phase 2 graph (memory recall → guardrail → five agents using
real-but-mocked tools + RAG → memory write) and prints findings, a priority-sorted CVE
table, similar past incidents, guardrail flags, and a cost summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from secops.graph import build_graph
from secops.state import CVEMatch, Incident, SecOpsState

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mock_incident.json"


def _load_incident(title: str | None) -> Incident:
    data = json.loads(FIXTURE.read_text())
    incident = Incident(**data)
    if title:
        incident.title = title
    return incident


def run(title: str | None, thread_id: str = "phase2") -> SecOpsState:
    """Execute the graph and return the final state."""
    graph = build_graph()
    initial = SecOpsState(incident=_load_incident(title))
    config = {"configurable": {"thread_id": thread_id}}
    final = graph.invoke(initial, config=config)
    return SecOpsState.model_validate(final)


def _dedupe_cves(matches: list) -> list[CVEMatch]:
    """Keep the highest-priority entry per CVE id, sorted by priority desc.

    Accepts ``CVEMatch`` objects (CLI) or plain dicts (checkpointer state values, which
    deserialize to dicts) interchangeably.
    """
    best: dict[str, CVEMatch] = {}
    for raw in matches:
        m = raw if isinstance(raw, CVEMatch) else CVEMatch(**raw)
        cur = best.get(m.cve_id)
        if cur is None or m.priority > cur.priority:
            best[m.cve_id] = m
    return sorted(best.values(), key=lambda m: m.priority, reverse=True)


def _print(state: SecOpsState) -> None:
    print(f"\n=== Incident: {state.incident.title} ===")
    print(f"Agents visited ({len(state.visited)}): {' -> '.join(state.visited)}")

    if state.similar_past:
        print("\n--- Similar past incidents ---")
        for h in state.similar_past:
            print(f"  • {h.get('title')}  (id={h.get('id')}, score={h.get('score')})")
    else:
        print("\n--- Similar past incidents --- (none yet)")

    print("\n--- Findings ---")
    for f in state.findings:
        print(f"  [{f.severity:>8}] {f.agent}: {f.title}")

    cves = _dedupe_cves(state.cve_matches)
    if cves:
        print("\n--- CVE matches (by priority) ---")
        print(f"  {'CVE':<16} {'CVSS':>5} {'EPSS':>5} {'KEV':>4} {'RNSM':>5} {'PRIO':>5}")
        for m in cves:
            print(
                f"  {m.cve_id:<16} {m.cvss or 0:>5} {m.epss or 0:>5} "
                f"{('Y' if m.in_kev else 'n'):>4} {('Y' if m.known_ransomware else 'n'):>5} "
                f"{m.priority:>5}"
            )

    print("\n--- Guardrail flags ---")
    if state.guardrail_flags:
        for fl in state.guardrail_flags:
            print(f"  ⚑ {fl}")
    else:
        print("  (none)")

    print("\n--- Cost (estimated tokens) ---")
    per = state.cost.get("per_agent", {})
    for node, tokens in per.items():
        print(f"  {node:<18} {tokens}")
    print(f"  {'TOTAL':<18} {state.cost.get('total', 0)}")

    print("\n--- Response Plan ---")
    print(state.response_plan or "(none)")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secops")
    sub = parser.add_subparsers(dest="command", required=True)
    run_p = sub.add_parser("run", help="Run the supervisor graph over the mock incident")
    run_p.add_argument("--incident", default=None, help="Incident title")
    sub.add_parser("index", help="(Re)build the RAG knowledge index in LanceDB")
    sub.add_parser("serve", help="Start the FastAPI server (uvicorn)")
    args = parser.parse_args(argv)

    if args.command == "run":
        _print(run(args.incident))
        return 0
    if args.command == "index":
        from secops.rag.index import build_index

        build_index()
        print("RAG knowledge index built.")
        return 0
    if args.command == "serve":
        import uvicorn

        from secops.config import get_settings

        s = get_settings()
        uvicorn.run("secops.server:app", host=s.api_host, port=s.api_port)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
