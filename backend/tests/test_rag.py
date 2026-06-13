"""RAG tests — build the index offline and retrieve relevant control passages."""

from __future__ import annotations


def test_knowledge_search_returns_relevant_controls(tmp_lancedb, embed_available):
    from secops.rag.index import build_index, knowledge_search

    build_index()

    patch = " ".join(knowledge_search("patch SLA for unpatched vulnerabilities", 3)).lower()
    assert "patch" in patch

    access = " ".join(knowledge_search("least privilege access control", 3)).lower()
    assert "access" in access or "privilege" in access
