"""Long-term memory tests — a similar (not identical) incident recalls the prior one."""

from __future__ import annotations

from secops.memory import memory_recall, memory_write
from secops.state import Finding, Incident, SecOpsState


def test_similar_incident_is_recalled(tmp_lancedb, embed_available):
    first = Incident(
        id="INC-A",
        title="Critical RCE in edge gateway",
        description="Unauthenticated remote code execution on the internet-facing gateway host.",
    )
    assert memory_recall(first) == []  # empty store

    state = SecOpsState(
        incident=first,
        response_plan="isolate + patch",
        findings=[Finding(agent="vuln_scanner", title="RCE")],
    )
    memory_write(state, created="2026-06-13")

    similar = Incident(
        id="INC-B",
        title="Remote code execution on gateway appliance",
        description="Attacker achieved RCE against the perimeter gateway.",
    )
    hits = memory_recall(similar)
    assert hits and hits[0]["id"] == "INC-A"
