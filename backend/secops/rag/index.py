"""LlamaIndex knowledge index over a seed corpus, stored in LanceDB.

Embeddings use a **local** HuggingFace model (no embedding API). ``Settings.llm`` is set
to ``None`` so retrieval never calls a chat LLM — the index stays fully offline once the
embedding weights are cached. "Agentic" retrieval = the calling agent node picks the
query and may call :func:`knowledge_search` more than once; the retriever itself is a
plain vector retriever.
"""

from __future__ import annotations

from pathlib import Path

from secops.config import get_settings

_CORPUS_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "corpus"
_TABLE = "knowledge"
_index_cache: dict[str, object] = {}
_configured = False


def _configure() -> None:
    """Point LlamaIndex at the local HF embedder and disable the LLM (offline).

    We assign ``Settings.embed_model`` directly (never read it first) because reading the
    default triggers LlamaIndex's lazy OpenAI resolver, which fails with no API key.
    """
    global _configured
    from llama_index.core import Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    if not _configured:
        Settings.embed_model = HuggingFaceEmbedding(model_name=get_settings().embed_model)
        _configured = True
    Settings.llm = None  # type: ignore[assignment]  # disable LLM → offline retrieval


def get_embed_model():
    """Return the shared, configured local HF embedder (reused by memory.py)."""
    _configure()
    from llama_index.core import Settings

    return Settings.embed_model


def _vector_store():
    from llama_index.vector_stores.lancedb import LanceDBVectorStore

    return LanceDBVectorStore(uri=get_settings().lancedb_dir, table_name=_TABLE)


def _table_has_rows() -> bool:
    import lancedb

    db = lancedb.connect(get_settings().lancedb_dir)
    if _TABLE not in db.table_names():
        return False
    return db.open_table(_TABLE).count_rows() > 0


def build_index():
    """(Re)build the knowledge index from the corpus and persist it to LanceDB."""
    from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex

    _configure()
    docs = SimpleDirectoryReader(str(_CORPUS_DIR)).load_data()
    storage = StorageContext.from_defaults(vector_store=_vector_store())
    index = VectorStoreIndex.from_documents(docs, storage_context=storage)
    _index_cache[get_settings().lancedb_dir] = index
    return index


def get_index():
    """Return a cached index, opening the existing table or building it if empty."""
    from llama_index.core import VectorStoreIndex

    uri = get_settings().lancedb_dir
    if uri in _index_cache:
        return _index_cache[uri]
    _configure()
    if not _table_has_rows():
        return build_index()
    index = VectorStoreIndex.from_vector_store(_vector_store())
    _index_cache[uri] = index
    return index


def knowledge_search(query: str, k: int | None = None) -> list[str]:
    """Return the top-k relevant passages for a query."""
    k = k or get_settings().rag_top_k
    nodes = get_index().as_retriever(similarity_top_k=k).retrieve(query)
    return [n.get_content().strip() for n in nodes]
