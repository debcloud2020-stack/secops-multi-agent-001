"""Long-term incident memory (LanceDB).

Completed runs (incident → findings → plan) are embedded with the same local HF model
and persisted to a LanceDB ``memory`` table. On a new incident, ``memory_recall`` returns
the top-k similar past incidents into ``state.similar_past`` to prime the agents.
"""

from __future__ import annotations

import json

from secops.config import get_settings
from secops.rag.index import get_embed_model
from secops.state import Incident, SecOpsState

_TABLE = "memory"


def _summary_text(incident: Incident) -> str:
    return f"{incident.title}. {incident.description}".strip()


def _embed(text: str) -> list[float]:
    return get_embed_model().get_text_embedding(text)


def _connect():
    import lancedb

    return lancedb.connect(get_settings().lancedb_dir)


def memory_recall(incident: Incident) -> list[dict]:
    """Return up to ``memory_top_k`` past incidents most similar to this one."""
    db = _connect()
    if _TABLE not in db.table_names():
        return []
    table = db.open_table(_TABLE)
    if table.count_rows() == 0:
        return []

    vector = _embed(_summary_text(incident))
    k = get_settings().memory_top_k
    rows = table.search(vector).limit(k).to_list()

    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "summary": r.get("summary"),
                "plan": r.get("plan"),
                "created": r.get("created"),
                "score": round(float(r.get("_distance", 0.0)), 4),
            }
        )
    return out


def memory_write(state: SecOpsState, created: str = "") -> None:
    """Persist a completed run to the memory table (creating it if needed)."""
    incident = state.incident
    record = {
        "id": incident.id,
        "title": incident.title,
        "summary": _summary_text(incident),
        "vector": _embed(_summary_text(incident)),
        "findings": json.dumps([f.model_dump() for f in state.findings]),
        "plan": state.response_plan or "",
        "created": created,
    }
    db = _connect()
    if _TABLE not in db.table_names():
        db.create_table(_TABLE, data=[record])
    else:
        db.open_table(_TABLE).add([record])
