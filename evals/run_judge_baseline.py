"""Measure the LLM-judge (plan_quality) baseline — requires a REAL model (costs money).

Runs the golden suite with a live LLM and prints the mean plan_quality (1-5 scale). Record
it in BASELINE.md and set the test floor to mean − 0.5 (export JUDGE_MEAN_FLOOR=<that>).

    cd backend && MOCK_MODE=false OPENROUTER_API_KEY=... \
      LLM_MODEL_CHEAP=... LLM_MODEL_STRONG=... \
      uv run python ../evals/run_judge_baseline.py

Unlike report_baseline.py this does NOT force mock mode — it honours MOCK_MODE=false so the
plans are really synthesized and really judged. Embeddings + LanceDB use a temp dir.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Run-as-script path fix (same as report_baseline.py): import siblings as the `evals`
# package and keep this dir off sys.path so evals/datasets/ can't shadow `datasets`.
_HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _HERE]
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))


def main() -> int:
    # Isolated LanceDB, but DO NOT touch MOCK_MODE (the judge needs the real model).
    os.environ["LANCEDB_DIR"] = str(Path(tempfile.mkdtemp(prefix="judge-baseline-")) / "lancedb")
    import secops.config as cfg

    cfg._settings = None
    settings = cfg.get_settings()
    if settings.mock_mode or not settings.openrouter_api_key:
        print("Set MOCK_MODE=false and OPENROUTER_API_KEY (+ LLM_MODEL_STRONG) to run the judge.")
        return 1

    from secops.rag.index import build_index

    build_index()

    from evals import evaluators as ev
    from evals.runner import load_golden, run_suite

    results = run_suite(load_golden())
    judged = [ev.plan_quality(example, state) for example, state in results]
    means = [r["mean5"] for r in judged if r is not None]
    if not means:
        print("plan_quality returned no scores (judge skipped?).")
        return 1

    mean = sum(means) / len(means)
    print(f"plan_quality baseline: mean={mean:.2f} over {len(means)} examples (1-5 scale)")
    print(f"  → record in BASELINE.md and set JUDGE_MEAN_FLOOR={max(0.0, mean - 0.5):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
