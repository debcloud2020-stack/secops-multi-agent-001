"""Golden-set eval gate — runs the graph once, scores every evaluator, asserts thresholds.

Thresholds are set against the measured baseline in ``BASELINE.md`` (measure-then-set).
Runs fully offline: deterministic + theme evaluators assert; the LLM-judge skips cleanly
without a real model. Mark the suite for LangSmith only when ``LANGSMITH_TRACING`` is set.

    cd backend && uv run pytest ../evals -q
"""

from __future__ import annotations

import os

import pytest

from evals import evaluators as ev
from evals.runner import load_golden

# --- Thresholds (derived from BASELINE.md — do not invent; re-measure if the graph changes) ---
COST_CEILING = 1700  # round-up of max baseline cost 1359 × 1.25 (≈1699)
JUDGE_MEAN_FLOOR = 3.0  # 1–5 scale; when a real baseline is measured, set to baseline_mean − 0.5

EXAMPLES = load_golden()
IDS = [e["id"] for e in EXAMPLES]

# Opt-in LangSmith tracing for the whole module (the marker is registered in conftest).
if os.getenv("LANGSMITH_TRACING"):
    pytestmark = pytest.mark.langsmith


@pytest.fixture(scope="session")
def by_id(suite) -> dict[str, tuple[dict, object]]:
    """Index the run-once suite results by example id."""
    return {example["id"]: (example, state) for example, state in suite}


# --- Deterministic evaluators (full pass) --------------------------------------------

@pytest.mark.parametrize("ex_id", IDS)
def test_agent_coverage(by_id, ex_id):
    example, state = by_id[ex_id]
    r = ev.agent_coverage(example, state)
    assert r["passed"], r["detail"]


@pytest.mark.parametrize("ex_id", IDS)
def test_plan_present(by_id, ex_id):
    example, state = by_id[ex_id]
    r = ev.plan_present(example, state)
    assert r["passed"], r["detail"]


@pytest.mark.parametrize("ex_id", IDS)
def test_severity_floor(by_id, ex_id):
    example, state = by_id[ex_id]
    r = ev.severity_floor(example, state)
    assert r["passed"], r["detail"]


@pytest.mark.parametrize("ex_id", IDS)
def test_keyword_coverage(by_id, ex_id):
    example, state = by_id[ex_id]
    r = ev.keyword_coverage(example, state)
    assert r["score"] == 1.0, r["detail"]


# --- Theme-specific evaluators -------------------------------------------------------

@pytest.mark.parametrize("ex_id", IDS)
def test_guardrail_catch_rate(by_id, ex_id):
    example, state = by_id[ex_id]
    r = ev.guardrail_catch_rate(example, state)
    assert r["passed"], r["detail"]


def test_guardrail_benign_passes():
    """Injected fixture flags; benign fixture passes clean (the 'benign passes' half)."""
    r = ev.guardrail_fixture_check()
    assert r["passed"], r["detail"]


@pytest.mark.parametrize("ex_id", IDS)
def test_memory_recall_relevance(by_id, ex_id):
    example, state = by_id[ex_id]
    r = ev.memory_recall_relevance(example, state)
    assert r["passed"], r["detail"]


@pytest.mark.parametrize("ex_id", IDS)
def test_cost_regression(by_id, ex_id):
    example, state = by_id[ex_id]
    r = ev.cost_regression(example, state, COST_CEILING)
    assert r["passed"], r["detail"]


# --- LLM-judge (degrades gracefully) -------------------------------------------------

def test_plan_quality_judge(suite):
    """Reference-free rubric — skips offline; asserts a mean floor when a judge runs."""
    results = [ev.plan_quality(example, state) for example, state in suite]
    if all(r is None for r in results):
        pytest.skip("LLM-judge skipped — no judge model (mock_mode / no OPENROUTER_API_KEY)")
    means = [r["mean5"] for r in results if r is not None]
    mean = sum(means) / len(means)
    assert mean >= JUDGE_MEAN_FLOOR, f"plan_quality mean {mean:.2f} < floor {JUDGE_MEAN_FLOOR}"


# --- Guard: the evaluators can actually fail (not trivially green) --------------------

def test_agent_coverage_detects_regression():
    from secops.state import Finding, Incident, SecOpsState

    example = {"expect": {"trajectory": ["log_monitor", "threat_intel"]}}
    bad = SecOpsState(
        incident=Incident(title="x"),
        visited=["log_monitor"],  # missing threat_intel → must fail
        findings=[Finding(agent="log_monitor", title="t")],
    )
    assert not ev.agent_coverage(example, bad)["passed"]
