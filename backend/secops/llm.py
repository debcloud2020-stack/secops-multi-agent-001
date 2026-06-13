"""LLM factories.

Real path: OpenRouter via ``langchain-openai`` ChatOpenAI (two tiers).
Offline path: a deterministic stub used in tests and whenever ``mock_mode`` is true or
no ``OPENROUTER_API_KEY`` is set. The stub is importable directly for tests.
"""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from secops.config import Settings, get_settings


class OfflineChatModel(BaseChatModel):
    """Deterministic offline chat model — no network, no API key.

    Returns a canned ``AIMessage`` tagged with its tier so callers/tests can assert
    which model was used. Good enough for Phase 1 mock routing and synthesis.
    """

    tier: str = "cheap"

    @property
    def _llm_type(self) -> str:
        return "secops-offline-stub"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        last = messages[-1].content if messages else ""
        text = f"[offline-stub:{self.tier}] {last}".strip()
        message = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=message)])


def _use_stub(settings: Settings) -> bool:
    return settings.mock_mode or not settings.openrouter_api_key


def _build(tier: str, model_id: str | None) -> BaseChatModel:
    settings = get_settings()
    if _use_stub(settings):
        return OfflineChatModel(tier=tier)

    # Real OpenRouter path (only reached when mock_mode is false AND a key is set).
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr

    return ChatOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=SecretStr(settings.openrouter_api_key or ""),
        model=model_id or "",
        temperature=0,
    )


def get_llm_cheap() -> BaseChatModel:
    """Supervisor / triage tier."""
    return _build("cheap", get_settings().llm_model_cheap)


def get_llm_strong() -> BaseChatModel:
    """Incident-response synthesis tier."""
    return _build("strong", get_settings().llm_model_strong)
