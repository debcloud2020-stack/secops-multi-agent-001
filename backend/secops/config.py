"""Typed application settings (pydantic-settings).

All values come from the environment or a local ``.env`` file. Model IDs are left as
env placeholders — never hardcode OpenRouter model IDs here.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


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


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
