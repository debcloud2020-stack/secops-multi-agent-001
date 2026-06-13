# SecOps Multi-Agent — backend (Phase 2, mock mode)

LangGraph supervisor that routes through five cybersecurity agents over mock-defaulted
real tools, with agentic RAG (LlamaIndex + LanceDB, local HF embeddings), a
prompt-injection guardrail, long-term memory, and token-cost accounting. Graph flow:
`memory_recall → guardrail → supervisor ⇄ [5 agents] → memory_write`. Default
`MOCK_MODE=true` is fully offline (LLM stubbed); the first RAG/memory use downloads the
`bge-small-en-v1.5` embedding model (~130 MB) to `~/.cache/huggingface`, then runs offline.

## Setup

```bash
uv python install 3.12   # once, if 3.12 isn't installed
cd backend
uv sync
```

## Run (mock mode)

```bash
uv run python -m secops.app run --incident "Critical RCE in gateway"
uv run python -m secops.app index   # (re)build the RAG knowledge index in LanceDB
```

`run` prints: agents visited (log_monitor → threat_intel → vuln_scanner →
policy_checker → incident_response), similar past incidents, per-agent findings, a
priority-sorted CVE table (CVSS/EPSS/KEV/ransomware/priority), guardrail flags, a cost
summary, and the synthesized response plan.

### Real LLM / live tools (optional)

Copy `.env.example` to `.env`, set `MOCK_MODE=false`, `OPENROUTER_API_KEY`, and the
`LLM_MODEL_CHEAP` / `LLM_MODEL_STRONG` model IDs to call OpenRouter. With `MOCK_MODE=false`
the tools also try their live paths (Azure Monitor / NVD-KEV-EPSS / trivy+pip-audit) and
fall back to the mock fixtures on any failure. Embeddings are always the local HF model.

## API server (Phase 3)

Start the local HTTP API (every endpoint requires the demo password):

```bash
export DEMO_PASSWORD=changeme
uv run uvicorn secops.server:app --port 8000      # or: uv run python -m secops.app serve
```

Auth: send `Authorization: Bearer $DEMO_PASSWORD` on every request (401 otherwise).
Endpoints (PLAN.md §10): `GET /health`, `GET /incidents`, `POST /runs`, `GET /runs/{id}`,
`GET /runs`, `POST /runs/{id}/approve`, `GET /threats`, `GET /compliance`.

Run → poll → approve flow:

```bash
H='Authorization: Bearer changeme'
curl -s -H "$H" localhost:8000/incidents                         # curated incident list
RID=$(curl -s -H "$H" -X POST localhost:8000/runs \
       -d '{"incident_id":"INC-1001","data_mode":"mock"}' | jq -r .run_id)
curl -s -H "$H" localhost:8000/runs/$RID                         # poll: status grows
# INC-1001 requires approval → status becomes "awaiting_approval":
curl -s -H "$H" -X POST localhost:8000/runs/$RID/approve \
     -d '{"decision":"approve"}'                                 # or {"decision":"reject"}
```

Curated incidents: `INC-1001` requires approval (HITL); `INC-1002`/`INC-1003` run
straight through to a plan. Runs execute in a background thread pool; `GET /runs/{id}`
reads the LangGraph checkpointer. Single-process only (in-memory checkpointer) — see
`server.py`.

## Verify

```bash
uv run ruff check .      # lint (blocking)
uv run pytest -q         # tests + smoke (blocking)
uv run mypy secops       # type-check (advisory — non-blocking)
```

RAG/memory tests auto-skip if the HF embedding model can't be loaded (offline/CI).

## Layout

- `secops/config.py` — pydantic-settings (mock_mode, embeddings, LanceDB, guardrail)
- `secops/llm.py` — OpenRouter factories + offline stub (`OfflineChatModel`)
- `secops/state.py` — `SecOpsState`, `Incident`/`Finding`/`CVEMatch`, `cve_matches`, reducers
- `secops/tools/` — `azure_logs` (KQL detections), `threat_intel` (enrich_cve), `scanner`
- `secops/rag/index.py` — LlamaIndex + LanceDB knowledge index, `knowledge_search`
- `secops/guardrail.py` — prompt-injection scan (pattern + optional LLM classifier)
- `secops/memory.py` — long-term incident recall/write (LanceDB)
- `secops/cost.py` — token estimation + accumulation into `state.cost`
- `secops/agents.py` — supervisor, feature-layer nodes, five agent nodes, `route()`
- `secops/graph.py` — `StateGraph` (memory → guardrail → supervisor ⇄ agents → write)
- `secops/app.py` — CLI (`run`, `index`)
- `fixtures/` — mock incident, tool fixtures, RAG corpus, guardrail samples
- `tests/` — tools, guardrail, memory, rag, cost, and the extended smoke test
