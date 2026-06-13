"""Agent tools — each has a live path and a mock-fixture path (mock is the default)."""

from __future__ import annotations

import json
from pathlib import Path

# …/backend/fixtures
FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"


def load_fixture(*parts: str) -> object:
    """Load a JSON fixture under backend/fixtures/."""
    return json.loads((FIXTURES.joinpath(*parts)).read_text())
