"""Optional LangSmith experiment entrypoint (offline-capable, guarded).

Only runs an actual LangSmith experiment when ``LANGSMITH_API_KEY`` is set; otherwise it
prints a skip message and exits 0. Not part of the pytest gate.

    cd backend && uv run python ../evals/experiment.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Run-as-script path fix: import siblings as the `evals` package from the repo root, and
# keep this dir OFF sys.path so `evals/datasets/` can't shadow the PyPI `datasets` package.
_HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from evals._bootstrap import force_offline_env  # noqa: E402


def main() -> int:
    if not os.getenv("LANGSMITH_API_KEY"):
        print("LangSmith not configured (no LANGSMITH_API_KEY) — skipping experiment.")
        return 0

    force_offline_env(Path(tempfile.mkdtemp(prefix="eval-experiment-")) / "lancedb")

    from langsmith import evaluate

    from evals import evaluators as ev
    from evals.runner import build_graph_and_index, load_golden

    graph = build_graph_and_index()
    golden = load_golden()
    by_id = {e["id"]: e for e in golden}

    def target(inputs: dict) -> dict:
        from evals.runner import run_example

        example = by_id[inputs["id"]]
        state = run_example(graph, example, thread_id=f"ls-{inputs['id']}")
        return {"state": state, "example": example}

    def _scorer(fn):
        def wrapped(run, example=None):
            out = run.outputs or {}
            r = fn(out["example"], out["state"])
            return {"key": r["name"], "score": r["score"]}

        wrapped.__name__ = fn.__name__
        return wrapped

    evaluate(
        target,
        data=[{"id": e["id"]} for e in golden],
        evaluators=[
            _scorer(ev.agent_coverage),
            _scorer(ev.plan_present),
            _scorer(ev.severity_floor),
            _scorer(ev.keyword_coverage),
        ],
        experiment_prefix="secops-golden",
    )
    print("LangSmith experiment submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
