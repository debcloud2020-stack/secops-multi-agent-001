"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

import secops.config as cfg


@pytest.fixture(autouse=True)
def _hermetic_env(monkeypatch):
    """Run tests offline + deterministic regardless of a local backend/.env (which may
    point at real Azure / OpenRouter). Real env vars override the dotenv file in
    pydantic-settings, so this forces mock mode and clears live creds for every test —
    matching CI (MOCK_MODE=true) and avoiding accidental paid LLM / cloud calls."""
    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("AZURE_WORKSPACE_ID", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("POSTGRES_DSN", "")
    cfg._settings = None
    yield
    cfg._settings = None


@pytest.fixture
def tmp_lancedb(tmp_path, monkeypatch):
    """Point LanceDB (knowledge + memory) at an isolated temp dir for this test."""
    monkeypatch.setenv("LANCEDB_DIR", str(tmp_path / "lancedb"))
    cfg._settings = None  # drop the cached Settings so the env override is picked up
    import secops.rag.index as idx

    idx._index_cache.clear()
    yield
    cfg._settings = None


@pytest.fixture(scope="session")
def embed_available():
    """Skip the test if the local HF embedding model can't be loaded (offline/CI)."""
    try:
        from secops.rag.index import get_embed_model

        get_embed_model().get_text_embedding("ping")
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"HF embedding model unavailable: {exc}")
    return True


@pytest.fixture
def api_client():
    """A TestClient for the open (no-auth) API."""
    from fastapi.testclient import TestClient

    from secops.server import app

    return TestClient(app)
