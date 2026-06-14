"""FastAPI API over the SecOps graph (Phase 3).

The API is open — no auth gate. Runs execute in a background thread pool so progress can be
polled; ``GET /runs/{id}`` reads the LangGraph checkpointer (the source of truth) via
``get_state``. A human-in-the-loop interrupt pauses approval-required runs;
``POST /runs/{id}/approve`` resumes them with ``Command(resume=...)``.

Single-process by design (in-memory ``MemorySaver`` + run registry). Cross-process polling
would need a shared checkpointer (Postgres) — deferred to Phase 5.
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command

from secops.app import _dedupe_cves
from secops.config import get_settings
from secops.graph import build_graph
from secops.schemas import (
    ApproveRequest,
    ComplianceOut,
    IncidentOut,
    RunCreated,
    RunRequest,
    RunStatus,
    RunStatusValue,
    RunSummary,
)
from secops.state import CVEMatch, DataMode, Incident, SecOpsState
from secops.tools import load_fixture

# --- Singletons (single-process; see module docstring) -------------------------------
log = logging.getLogger(__name__)
GRAPH = build_graph()
RUNS: dict[str, dict] = {}
_LOCK = threading.Lock()  # guards RUNS reads/writes/iteration across threads
_EXECUTOR = ThreadPoolExecutor(max_workers=4)


app = FastAPI(title="SecOps Multi-Agent API")

# CORS so the browser (Next.js dev on :3000) can call the API. The app is open (no auth);
# OPTIONS preflight is allowed; credentials are not used.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


# --- Helpers -------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(UTC).isoformat()


def _cfg(run_id: str) -> dict:
    return {"configurable": {"thread_id": run_id}}


def _curated() -> list[dict]:
    return load_fixture("incidents.json")  # type: ignore[return-value]


def _incident_by_id(incident_id: str) -> Incident:
    entry = next((i for i in _curated() if i["id"] == incident_id), None)
    if entry is None:
        raise HTTPException(status_code=400, detail="unknown incident_id (not in curated list)")
    return Incident(**entry)


def _record_error(run_id: str, exc: Exception) -> None:
    # Log the real exception server-side; expose only a generic message to clients so
    # paths/keys/internal details from the graph run never leak in the API response.
    log.exception("run %s failed: %s", run_id, exc)
    with _LOCK:
        RUNS[run_id]["error"] = "run failed"
        # Release the resume lock so a failed resume doesn't 409-lock the run forever;
        # the run now reports status "error" (checked before interrupts in _status).
        RUNS[run_id]["resuming"] = False


def _start_run(run_id: str, incident: Incident, data_mode: DataMode) -> None:
    def task() -> None:
        try:
            GRAPH.invoke(SecOpsState(incident=incident, data_mode=data_mode), _cfg(run_id))
        except Exception as exc:  # noqa: BLE001 — surface as run error, don't crash server.
            _record_error(run_id, exc)

    _EXECUTOR.submit(task)


def _resume_run(run_id: str, resume_value: dict) -> None:
    def task() -> None:
        try:
            GRAPH.invoke(Command(resume=resume_value), _cfg(run_id))
        except Exception as exc:  # noqa: BLE001
            _record_error(run_id, exc)

    _EXECUTOR.submit(task)


def _status(run_id: str, snap) -> RunStatusValue:
    if RUNS[run_id].get("error"):
        return "error"
    if snap.interrupts:
        return "awaiting_approval"
    if not snap.values:  # no checkpoint written yet
        return "queued"
    if snap.next:
        return "running"
    decision = (snap.values.get("approval") or {}).get("decision")
    return "rejected" if decision == "reject" else "completed"


def _build_status(run_id: str) -> RunStatus:
    reg = RUNS[run_id]
    snap = GRAPH.get_state(_cfg(run_id))
    v = snap.values or {}
    return RunStatus(
        run_id=run_id,
        status=_status(run_id, snap),
        incident_id=reg["incident_id"],
        data_mode=v.get("data_mode") or reg["data_mode"],
        data_notices=list(dict.fromkeys(v.get("data_notices", []))),  # de-duped, order-stable
        source_rows=v.get("source_rows"),
        visited=v.get("visited", []),
        findings=v.get("findings", []),
        cve_matches=_dedupe_cves(v.get("cve_matches", [])),
        cost=v.get("cost", {}),
        guardrail_flags=v.get("guardrail_flags", []),
        similar_past=v.get("similar_past", []),
        plan=v.get("response_plan"),
        error=reg.get("error"),
    )


# --- Endpoints (PLAN.md §10) ---------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/incidents", response_model=list[IncidentOut])
def incidents() -> list[dict]:
    return _curated()


@app.post("/runs", response_model=RunCreated, status_code=201)
def start_run(req: RunRequest) -> RunCreated:
    incident = _incident_by_id(req.incident_id)
    run_id = uuid4().hex
    with _LOCK:
        RUNS[run_id] = {
            "incident_id": req.incident_id,
            "data_mode": req.data_mode,
            "created": _now(),
            "error": None,
            "resuming": False,
        }
    _start_run(run_id, incident, req.data_mode)
    return RunCreated(run_id=run_id)


@app.get("/runs", response_model=list[RunSummary])
def list_runs() -> list[RunSummary]:
    with _LOCK:
        items = list(RUNS.items())  # snapshot to iterate safely while runs mutate
    out = []
    for run_id, reg in items:
        snap = GRAPH.get_state(_cfg(run_id))
        out.append(
            RunSummary(
                run_id=run_id,
                incident_id=reg["incident_id"],
                status=_status(run_id, snap),
                created=reg["created"],
            )
        )
    return out


@app.get("/runs/{run_id}", response_model=RunStatus)
def get_run(run_id: str = Path(...)) -> RunStatus:
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="run not found")
    return _build_status(run_id)


@app.post("/runs/{run_id}/approve", response_model=RunStatus)
def approve_run(run_id: str, req: ApproveRequest) -> RunStatus:
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="run not found")
    snap = GRAPH.get_state(_cfg(run_id))
    if not snap.interrupts:
        raise HTTPException(status_code=409, detail="run is not awaiting approval")
    # Serialize the decision so only the first approve/reject wins (no double-resume).
    with _LOCK:
        if RUNS[run_id].get("resuming"):
            raise HTTPException(status_code=409, detail="run is already being resumed")
        RUNS[run_id]["resuming"] = True
    _resume_run(run_id, {"decision": req.decision, "edited_plan": req.edited_plan})
    return _build_status(run_id)


@app.get("/threats", response_model=list[CVEMatch])
def threats() -> list[CVEMatch]:
    with _LOCK:
        run_ids = list(RUNS)  # snapshot to iterate safely
    collected: list[CVEMatch] = []
    for run_id in run_ids:
        snap = GRAPH.get_state(_cfg(run_id))
        collected.extend((snap.values or {}).get("cve_matches", []))
    return _dedupe_cves(collected)


@app.get("/compliance", response_model=ComplianceOut)
def compliance() -> dict:
    return load_fixture("compliance.json")  # type: ignore[return-value]
