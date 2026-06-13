"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

import secops.config as cfg


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
def demo_password(monkeypatch):
    """Set the API demo password and reset the cached Settings so it's picked up."""
    pw = "test-pw-123"
    monkeypatch.setenv("DEMO_PASSWORD", pw)
    cfg._settings = None
    yield pw
    cfg._settings = None


@pytest.fixture
def api_client(demo_password):
    """A TestClient plus the auth header dict."""
    from fastapi.testclient import TestClient

    from secops.server import app

    return TestClient(app), {"Authorization": f"Bearer {demo_password}"}
