# evals — offline evaluation harness (Phase 5a)

A golden-set eval suite over the SecOps LangGraph, scored by deterministic + theme-specific
+ LLM-judge evaluators with thresholds set against a measured baseline. Runs fully offline
(`MOCK_MODE=true`, mock tools, local HF embeddings); the LLM-judge skips cleanly without a key.

## Run it (uses the backend uv environment)

```bash
cd backend && uv run pytest ../evals -q
```

Backend + evals together (the verify gate):

```bash
cd backend
uv run ruff check . ../evals
uv run pytest tests ../evals -q
```

The suite **skips** if the local HF embedding model (`BAAI/bge-small-en-v1.5`) can't be
loaded (first run downloads it; thereafter it's cached and works offline).

## Layout

| File | Purpose |
|---|---|
| `datasets/golden.jsonl` | 8 hand-labeled examples (approval, injected-log, similar-incident pair, straight-through). |
| `runner.py` | Runs the graph over the set in order on one shared graph + LanceDB (so the memory pair works); auto-approves a HITL pause. |
| `evaluators.py` | Deterministic (`agent_coverage`, `plan_present`, `severity_floor`, `keyword_coverage`), theme (`guardrail_catch_rate`, `memory_recall_relevance`, `cost_regression`), and LLM-judge (`plan_quality`, skips without a key). |
| `test_agents.py` | The pytest gate; encodes thresholds from `BASELINE.md`. |
| `report_baseline.py` | Prints the measured baseline table (`uv run python ../evals/report_baseline.py`). |
| `experiment.py` | Optional LangSmith experiment — runs only when `LANGSMITH_API_KEY` is set, else skips. |
| `BASELINE.md` | The recorded baseline + the thresholds derived from it. |

## Env toggles

- `MOCK_MODE=true` (default) — offline LLM stub + mock tools.
- `OPENROUTER_API_KEY` + `LLM_MODEL_STRONG` — enable the `plan_quality` LLM-judge (otherwise it skips).
- `LANGSMITH_TRACING=true` — marks the suite for LangSmith tracing.
- `LANGSMITH_API_KEY` — enables `experiment.py`.

## CI

`.github/workflows/eval.yml` runs this gate on PRs + nightly in `MOCK_MODE`. It is
**dormant** until the repo is pushed (Phase 5b) — do not trigger it before then.
