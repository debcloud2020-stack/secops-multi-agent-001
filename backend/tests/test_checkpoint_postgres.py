"""Postgres checkpointer persistence + HITL resume (Phase 5b-1).

Gated: runs only when ``POSTGRES_DSN`` is set (e.g. against a local or Azure Postgres).
Skipped in the normal offline gate.

    POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/postgres \
      uv run pytest tests/test_checkpoint_postgres.py -q
"""

from __future__ import annotations

import os

import pytest

from secops.state import Incident, SecOpsState

POSTGRES_DSN = os.getenv("POSTGRES_DSN")

pytestmark = pytest.mark.skipif(
    not POSTGRES_DSN, reason="POSTGRES_DSN not set — Postgres checkpointer test skipped"
)


def _build_graph_on(dsn: str):
    """Compile a graph whose checkpointer points at the given Postgres DSN."""
    import secops.config as cfg

    cfg._settings = None
    os.environ["POSTGRES_DSN"] = dsn
    from secops.graph import build_graph

    return build_graph()


def test_state_persists_and_hitl_resumes_across_savers(tmp_lancedb, embed_available):
    """A run paused at HITL is resumable from a freshly-built saver on the same DSN."""
    from langgraph.types import Command

    dsn = POSTGRES_DSN
    thread_id = "pg-hitl-001"
    cfg = {"configurable": {"thread_id": thread_id}}

    # First saver: run an approval-required incident to the HITL pause.
    graph_a = _build_graph_on(dsn)
    graph_a.invoke(
        SecOpsState(
            incident=Incident(id="INC-PG", title="Critical RCE", requires_approval=True)
        ),
        cfg,
    )
    assert graph_a.get_state(cfg).interrupts  # paused, persisted to Postgres

    # Second saver (simulates a process restart): the checkpoint is read back from Postgres.
    graph_b = _build_graph_on(dsn)
    snap = graph_b.get_state(cfg)
    assert snap.interrupts, "checkpoint did not persist across savers"

    # Resume the approval from the persisted checkpoint → completes with a plan.
    graph_b.invoke(Command(resume={"decision": "approve", "edited_plan": None}), cfg)
    done = graph_b.get_state(cfg)
    assert not done.interrupts
    assert done.values.get("response_plan")
