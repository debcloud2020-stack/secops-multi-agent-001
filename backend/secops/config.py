"""Typed application settings (pydantic-settings).

All values come from the environment or a local ``.env`` file. Model IDs are left as
env placeholders — never hardcode OpenRouter model IDs here.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Backend package root (…/backend), used to resolve default data paths.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Runtime configuration for the SecOps backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # When true (default), run fully offline: no cloud, no real LLM calls.
    mock_mode: bool = True

    # OpenRouter (OpenAI-compatible) connection.
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str | None = None

    # Two model tiers — set the concrete OpenRouter IDs in your environment.
    llm_model_cheap: str | None = None   # supervisor / triage
    llm_model_strong: str | None = None  # incident-response synthesis

    # Hard bound on supervisor routing iterations (loop guard / spend cap).
    max_supervisor_steps: int = 12

    # --- Phase 2: RAG + memory + guardrail ---
    # Local HuggingFace embedding model (a local resource — used in mock and live mode).
    embed_model: str = "BAAI/bge-small-en-v1.5"
    # LanceDB directory (knowledge + memory tables). Overridable for tests.
    lancedb_dir: str = str(_BACKEND_ROOT / ".data" / "lancedb")
    rag_top_k: int = 4
    memory_top_k: int = 3
    # Guardrail: enabled scans untrusted text; block=false keeps the run flowing
    # (flag-not-block) so suspicious content is quarantined, not executed.
    guardrail_enabled: bool = True
    guardrail_block: bool = False

    # Optional live-path settings (only used when mock_mode is false).
    azure_workspace_id: str | None = None
    nvd_api_key: str | None = None

    # --- Phase 3: API server ---
    # Demo password gate for every endpoint (Authorization: Bearer <demo_password>).
    # If unset, the gate fails closed (every request is rejected).
    demo_password: str | None = None
    api_host: str = "127.0.0.1"
    api_port: int = 8000


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
