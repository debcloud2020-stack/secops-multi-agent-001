"""Lightweight token accounting.

Estimate tokens per node and accumulate into ``state.cost`` (``{per_agent, total}``),
which uses the ``merge_cost`` reducer in state.py. Uses tiktoken when available, with a
character-based heuristic fallback so it works fully offline.
"""

from __future__ import annotations

_encoder = None
_encoder_tried = False


def estimate_tokens(text: str) -> int:
    """Estimate the token count of a string."""
    global _encoder, _encoder_tried
    if not text:
        return 0
    if not _encoder_tried:
        _encoder_tried = True
        try:
            import tiktoken

            _encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:  # noqa: BLE001 — fall back to a heuristic.
            _encoder = None
    if _encoder is not None:
        return len(_encoder.encode(text))
    # ~4 characters per token is a reasonable offline heuristic.
    return max(1, len(text) // 4)


def cost_update(node: str, *texts: str) -> dict:
    """Build a cost delta for one node: ``{per_agent: {node: n}, total: n}``."""
    tokens = sum(estimate_tokens(t) for t in texts if t)
    return {"per_agent": {node: tokens}, "total": tokens}
