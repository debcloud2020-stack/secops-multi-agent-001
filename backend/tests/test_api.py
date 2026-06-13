"""FastAPI API tests (TestClient, offline/mock)."""

from __future__ import annotations

import time

import pytest

# (method, path) for every gated endpoint.
ENDPOINTS = [
    ("get", "/health"),
    ("get", "/incidents"),
    ("post", "/runs"),
    ("get", "/runs"),
    ("get", "/runs/abc"),
    ("post", "/runs/abc/approve"),
    ("get", "/threats"),
    ("get", "/compliance"),
]


def _poll(client, headers, run_id, want, timeout=90.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = client.get(f"/runs/{run_id}", headers=headers).json()
        if last["status"] in want:
            return last
        time.sleep(0.5)
    return last


# --- Auth ----------------------------------------------------------------------------

@pytest.mark.parametrize("method,path", ENDPOINTS)
def test_every_endpoint_401_without_password(api_client, method, path):
    client, _ = api_client
    resp = getattr(client, method)(path)
    assert resp.status_code == 401


def test_health_ok_with_password_and_401_when_wrong(api_client):
    client, headers = api_client
    assert client.get("/health", headers=headers).json() == {"status": "ok"}
    assert client.get("/health", headers={"Authorization": "Bearer wrong"}).status_code == 401


# --- Curated incidents ---------------------------------------------------------------

def test_incidents_list_and_curated_enforcement(api_client):
    client, headers = api_client
    ids = {i["id"] for i in client.get("/incidents", headers=headers).json()}
    assert {"INC-1001", "INC-1002"}.issubset(ids)
    bad = client.post("/runs", headers=headers, json={"incident_id": "NOPE"})
    assert bad.status_code == 400


# --- Shapes (no graph run needed) ----------------------------------------------------

def test_threats_and_compliance_shape(api_client):
    client, headers = api_client
    threats = client.get("/threats", headers=headers)
    assert threats.status_code == 200 and isinstance(threats.json(), list)
    comp = client.get("/compliance", headers=headers).json()
    assert [f["name"] for f in comp["frameworks"]]
    assert "status" in comp["frameworks"][0]["controls"][0]


# --- Full lifecycle via polling (needs embeddings) -----------------------------------

def test_run_lifecycle_polls_to_completion(api_client, tmp_lancedb, embed_available):
    client, headers = api_client
    run_id = client.post(
        "/runs", headers=headers, json={"incident_id": "INC-1002"}
    ).json()["run_id"]

    result = _poll(client, headers, run_id, {"completed", "error"})
    assert result["status"] == "completed", result
    assert len(result["visited"]) == 5
    assert result["plan"]
    assert result["cost"].get("total", 0) > 0
    assert any(m["cve_id"] == "CVE-2026-00000" for m in result["cve_matches"])
    assert result["guardrail_flags"]


def test_hitl_approve_resumes_to_completion(api_client, tmp_lancedb, embed_available):
    client, headers = api_client
    run_id = client.post(
        "/runs", headers=headers, json={"incident_id": "INC-1001"}
    ).json()["run_id"]

    paused = _poll(client, headers, run_id, {"awaiting_approval", "error"})
    assert paused["status"] == "awaiting_approval"

    ok = client.post(f"/runs/{run_id}/approve", headers=headers, json={"decision": "approve"})
    assert ok.status_code == 200

    done = _poll(client, headers, run_id, {"completed", "error"})
    assert done["status"] == "completed" and done["plan"]


def test_hitl_reject_ends_cleanly(api_client, tmp_lancedb, embed_available):
    client, headers = api_client
    run_id = client.post(
        "/runs", headers=headers, json={"incident_id": "INC-1001"}
    ).json()["run_id"]
    _poll(client, headers, run_id, {"awaiting_approval"})

    client.post(f"/runs/{run_id}/approve", headers=headers, json={"decision": "reject"})
    done = _poll(client, headers, run_id, {"rejected", "completed"})
    assert done["status"] == "rejected"
    assert "REJECTED" in (done["plan"] or "")


def test_approve_non_awaiting_run_is_409(api_client):
    client, headers = api_client
    # A run id that exists but isn't awaiting approval is 409; unknown id is 404.
    assert client.post(
        "/runs/does-not-exist/approve", headers=headers, json={"decision": "approve"}
    ).status_code == 404
