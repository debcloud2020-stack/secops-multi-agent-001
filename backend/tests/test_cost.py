"""Cost accounting tests."""

from __future__ import annotations

from secops.cost import cost_update, estimate_tokens


def test_estimate_tokens_positive_for_nonempty():
    assert estimate_tokens("hello world, this is a test") > 0
    assert estimate_tokens("") == 0


def test_cost_update_shape():
    delta = cost_update("threat_intel", "some text", "more text")
    assert delta["per_agent"]["threat_intel"] > 0
    assert delta["total"] == delta["per_agent"]["threat_intel"]
