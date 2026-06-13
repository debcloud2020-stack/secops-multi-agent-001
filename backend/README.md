# SecOps Multi-Agent — backend (Phase 1, mock mode)

LangGraph supervisor that routes through five cybersecurity agent stubs over mock data.
Phase 1 is fully offline: no cloud, no real LLM (the LLM is stubbed).

## Setup

```bash
uv python install 3.12   # once, if 3.12 isn't installed
cd backend
uv sync
```

## Run (mock mode)

```bash
uv run python -m secops.app run --incident "Critical RCE in gateway"
```

Prints the agents visited (log_monitor → threat_intel → vuln_scanner → policy_checker →
incident_response), the per-agent findings, and a synthesized response plan.

### Real LLM (optional)

Copy `.env.example` to `.env`, set `MOCK_MODE=false`, `OPENROUTER_API_KEY`, and the
`LLM_MODEL_CHEAP` / `LLM_MODEL_STRONG` model IDs. The same command then calls OpenRouter.

## Verify

```bash
uv run ruff check .      # lint (blocking)
uv run pytest -q         # tests + smoke (blocking)
uv run mypy secops       # type-check (advisory — non-blocking in Phase 1)
```

## Layout

- `secops/config.py` — pydantic-settings configuration
- `secops/llm.py` — OpenRouter factories + offline stub (`OfflineChatModel`)
- `secops/state.py` — `SecOpsState` + `Incident` / `Finding` / `CVEMatch`
- `secops/agents.py` — supervisor router, five mock agent nodes, `route()`
- `secops/graph.py` — `StateGraph` + `MemorySaver`
- `secops/app.py` — CLI
- `fixtures/mock_incident.json` — mock incident
- `tests/test_smoke.py` — Phase 1 smoke test
