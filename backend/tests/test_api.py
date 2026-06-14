"""FastAPI API tests (TestClient, offline/mock). The API is open — no auth header."""

from __future__ import annotations

import time


def _poll(client, run_id, want, timeout=90.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = client.get(f"/runs/{run_id}").json()
        if last["status"] in want:
            return last
        time.sleep(0.5)
    return last


# --- Curated incidents ---------------------------------------------------------------

def test_incidents_list_and_curated_enforcement(api_client):
    ids = {i["id"] for i in api_client.get("/incidents").json()}
    assert {"INC-1001", "INC-1002"}.issubset(ids)
    bad = api_client.post("/runs", json={"incident_id": "NOPE"})
    assert bad.status_code == 400


# --- Shapes (no graph run needed) ----------------------------------------------------

def test_health_ok(api_client):
    assert api_client.get("/health").json() == {"status": "ok"}


def test_threats_and_compliance_shape(api_client):
    threats = api_client.get("/threats")
    assert threats.status_code == 200 and isinstance(threats.json(), list)
    comp = api_client.get("/compliance").json()
    assert [f["name"] for f in comp["frameworks"]]
    assert "status" in comp["frameworks"][0]["controls"][0]


# --- Full lifecycle via polling (needs embeddings) -----------------------------------

def test_run_lifecycle_polls_to_completion(api_client, tmp_lancedb, embed_available):
    run_id = api_client.post("/runs", json={"incident_id": "INC-1002"}).json()["run_id"]

    result = _poll(api_client, run_id, {"completed", "error"})
    assert result["status"] == "completed", result
    assert len(result["visited"]) == 5
    assert result["plan"]
    assert result["cost"].get("total", 0) > 0
    assert any(m["cve_id"] == "CVE-2026-00000" for m in result["cve_matches"])
    assert result["guardrail_flags"]


def test_hitl_approve_resumes_to_completion(api_client, tmp_lancedb, embed_available):
    run_id = api_client.post("/runs", json={"incident_id": "INC-1001"}).json()["run_id"]

    paused = _poll(api_client, run_id, {"awaiting_approval", "error"})
    assert paused["status"] == "awaiting_approval"

    ok = api_client.post(f"/runs/{run_id}/approve", json={"decision": "approve"})
    assert ok.status_code == 200

    done = _poll(api_client, run_id, {"completed", "error"})
    assert done["status"] == "completed" and done["plan"]


def test_hitl_reject_ends_cleanly(api_client, tmp_lancedb, embed_available):
    run_id = api_client.post("/runs", json={"incident_id": "INC-1001"}).json()["run_id"]
    _poll(api_client, run_id, {"awaiting_approval"})

    api_client.post(f"/runs/{run_id}/approve", json={"decision": "reject"})
    done = _poll(api_client, run_id, {"rejected", "completed"})
    assert done["status"] == "rejected"
    assert "REJECTED" in (done["plan"] or "")


def test_approve_unknown_run_is_404(api_client):
    assert api_client.post(
        "/runs/does-not-exist/approve", json={"decision": "approve"}
    ).status_code == 404
