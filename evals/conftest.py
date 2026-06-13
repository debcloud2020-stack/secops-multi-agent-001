"""Pytest fixtures for the offline eval harness.

Mirrors ``backend/tests/conftest.py``: forces mock mode + an isolated LanceDB dir,
skips when the local HF embedding model can't load, and builds the RAG index once. The
``golden`` + ``suite`` fixtures run the graph over the dataset a single time per session.
"""

from __future__ import annotations

import pytest

from evals._bootstrap import force_offline_env


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "langsmith: mark an eval test for LangSmith tracing (opt-in)"
    )


@pytest.fixture(scope="session")
def eval_env(tmp_path_factory: pytest.TempPathFactory):
    """Pin the process to mock mode + a temp LanceDB dir for the whole session."""
    force_offline_env(tmp_path_factory.mktemp("eval-lancedb"))
    yield
    import secops.config as cfg

    cfg._settings = None


@pytest.fixture(scope="session")
def embed_available(eval_env):
    """Skip the eval suite if the local HF embedding model can't be loaded (offline/CI)."""
    try:
        from secops.rag.index import get_embed_model

        get_embed_model().get_text_embedding("ping")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"HF embedding model unavailable: {exc}")
    return True


@pytest.fixture(scope="session")
def rag_index(embed_available):
    """Build the knowledge index once so agent retrieval is warm."""
    from secops.rag.index import build_index

    build_index()
    return True


@pytest.fixture(scope="session")
def golden() -> list[dict]:
    from evals.runner import load_golden

    return load_golden()


@pytest.fixture(scope="session")
def suite(rag_index, golden) -> list[tuple[dict, object]]:
    """Run the full golden set once (in order, shared graph + memory) for all tests."""
    from evals.runner import run_suite

    return run_suite(golden)
