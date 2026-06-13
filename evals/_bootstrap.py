"""Shared bootstrap for the offline eval harness.

Importing this module puts the backend package (``…/backend``) on ``sys.path`` so
``import secops`` works regardless of the pytest rootdir or the script's cwd. It also
exposes :func:`force_offline_env`, which pins the process to mock mode and an isolated
LanceDB directory (used by both ``conftest.py`` and the standalone report scripts).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVALS_DIR.parent / "backend"
GOLDEN_PATH = EVALS_DIR / "datasets" / "golden.jsonl"

# Make `import secops` resolve to the backend package whatever the caller's cwd/rootdir.
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def force_offline_env(lancedb_dir: str | os.PathLike[str]) -> None:
    """Pin mock mode + an isolated LanceDB dir, and drop cached Settings / RAG indexes."""
    os.environ["MOCK_MODE"] = "true"
    os.environ["LANCEDB_DIR"] = str(lancedb_dir)

    import secops.config as cfg

    cfg._settings = None  # re-read env on next get_settings()

    import secops.rag.index as idx

    idx._index_cache.clear()
