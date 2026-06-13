"""Measure the golden-set baseline (offline) — run BEFORE setting thresholds.

Runs the suite + every non-judge evaluator and prints a table plus the observed max/mean
cost. Paste the output into ``BASELINE.md``; the cost ceiling in ``test_agents.py`` is
derived from the max cost here. The LLM-judge runs only if a real model is configured.

    cd backend && uv run python ../evals/report_baseline.py
"""

from __future__ import annotations

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
    force_offline_env(Path(tempfile.mkdtemp(prefix="eval-baseline-")) / "lancedb")

    try:
        from secops.rag.index import build_index, get_embed_model

        get_embed_model().get_text_embedding("ping")
    except Exception as exc:  # noqa: BLE001
        print(f"HF embedding model unavailable — cannot measure baseline: {exc}")
        return 1
    build_index()

    from evals import evaluators as ev
    from evals.runner import load_golden, run_suite

    results = run_suite(load_golden())

    header = f"| {'id':<20} | traj | sev | kw% | guard | mem | cost |"
    sep = "|" + "-" * (len(header) - 2) + "|"
    print(header)
    print(sep)

    costs: list[int] = []
    for example, state in results:
        cov = ev.agent_coverage(example, state)
        sev = ev.severity_floor(example, state)
        kw = ev.keyword_coverage(example, state)
        guard = ev.guardrail_catch_rate(example, state)
        mem = ev.memory_recall_relevance(example, state)
        total = int(state.cost.get("total", 0))
        costs.append(total)
        print(
            f"| {example['id']:<20} | {_yn(cov['passed'])}    "
            f"| {_yn(sev['passed'])}   | {kw['score'] * 100:>3.0f} "
            f"| {_yn(guard['passed'])}     | {_yn(mem['passed'])}   | {total:>4} |"
        )

    fx = ev.guardrail_fixture_check()
    print()
    print(f"guardrail_fixture (injected / benign): {fx['detail']} -> {_yn(fx['passed'])}")
    print(f"cost: max={max(costs)} mean={sum(costs) // len(costs)} (ceiling = round_up(max*1.25))")
    print("plan_quality (LLM-judge): skipped offline (mock_mode / no OPENROUTER_API_KEY)")
    return 0


def _yn(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


if __name__ == "__main__":
    raise SystemExit(main())
