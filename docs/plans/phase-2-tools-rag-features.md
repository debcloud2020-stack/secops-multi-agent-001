# Phase 2 — Tools, RAG, guardrail, memory, cost

Status: **in progress**. Mock-first & local: default `MOCK_MODE=true`, no API, no
frontend, no cloud, no GitHub push.

## Context
Phase 1 delivered a LangGraph supervisor over five **mock** agent nodes, with
`similar_past` / `guardrail_flags` / `cost` as no-op state fields. Phase 2 turns those
into real (mock-defaulted) capabilities, adds agentic RAG (LlamaIndex + LanceDB, local
HF embeddings), and implements guardrail / memory / cost — then rewires the graph to
`START → memory_recall → guardrail → supervisor ⇄ [5 agents] → memory_write → END`
(matches PLAN.md §5).

## Decisions
- **Local HF embeddings (`BAAI/bge-small-en-v1.5`) are a local resource, used in both
  mock and live mode.** `MOCK_MODE` switches only the data tools + chat LLM. First run
  downloads ~130 MB to `~/.cache/huggingface`, then offline. RAG/memory tests skip with a
  clear message only if the model is neither cached nor downloadable.
- **`cve_matches[]` is a first-class state field** (PLAN.md §5/§9/§10), separate from
  `findings[]`, populated by `threat_intel` + `vuln_scanner`, surfaced priority-sorted.
- **Live → mock auto-fallback** in every tool (PLAN.md §7).
- LanceDB data in `backend/.data/lancedb/` (gitignored, env-overridable for tests); two
  tables: `knowledge` (RAG) + `memory` (incidents).
- Guardrail runs as a **node** (incident text, pre-supervisor) and a **function** agents
  call on tool output; **flag-not-block** default; pattern-only in mock (LLM classifier
  engages with `MOCK_MODE=false`).
- `CVEMatch` gains `in_kev`/`known_ransomware`/`priority`; `kev` → `in_kev`.
- `mypy` advisory; blocking gate = ruff + pytest + smoke. Confirm LlamaIndex/LanceDB API
  via context7 during implementation. Use security-reviewer subagent on `guardrail.py`.
- **Deferred to later phases** (per PLAN.md): `init_chat_model` + prompt-caching, Postgres
  checkpointer (keep `MemorySaver`), synthetic `data_mode`/Logs-Ingestion, and the HITL
  approval interrupt + `/approve` (now tracked under **Phase 3** in CLAUDE.md).

## New deps
`llama-index`, `llama-index-vector-stores-lancedb`,
`llama-index-embeddings-huggingface`, `lancedb`, `sentence-transformers` (pulls `torch`),
`azure-monitor-query`, `azure-identity`, `httpx`, `tiktoken`.

## Steps (summary)
0. Reconcile CLAUDE.md phase map (HITL+`/approve` under P3); this mirror file.
1. Deps + config (`embed_model`, `lancedb_dir`, guardrail/top-k flags) + state
   (`CVEMatch` fields, `cve_matches`, reducers) + `.gitignore`/`.env.example`.
2. Fixtures + seed corpus (NIST CSF/ISO 27001/SOC 2 + advisories; injected/benign).
3. `tools/azure_logs.py` — curated named KQL detections; live `LogsQueryClient` + fallback.
4. `tools/threat_intel.py` — `enrich_cve` (NVD/KEV/EPSS) →
   `priority = cvss*0.3 + epss*10*0.3 + (3 if KEV) + (1 if ransomware)`.
5. `tools/scanner.py` — trivy + pip-audit subprocess, normalized; mock + fallback.
6. `rag/index.py` — LlamaIndex over corpus in LanceDB (`Settings.llm=None`);
   `knowledge_search()`.
7. `guardrail.py` — pattern + optional LLM classifier; security-reviewer review.
8. `memory.py` — `memory_recall` / `memory_write` via LanceDB.
9. `cost.py` — `estimate_tokens` + `add_cost` into `state.cost`.
10. Wire `agents.py` — agents call tools through guardrail; populate `cve_matches`; cost.
11. Wire `graph.py` (new flow) + `app.py` (cve table, similar_past, flags, cost; `index`
    subcommand).
12. Tests — tools/guardrail/memory/rag/cost + extended smoke.
13. Verify gate (ruff + pytest + smoke; mypy advisory) + one local commit (no push).

## Verify / DoD
```bash
cd backend && uv run python -m secops.app run --incident "Critical RCE in gateway"
uv run ruff check . && uv run pytest -q
```
Runs `memory_recall → guardrail → five agents (mocked tools + RAG) → memory_write`;
prints findings, a priority-sorted `cve_matches` table, `similar_past`, `guardrail_flags`,
and a cost summary. Injected line flagged, benign passes; a similar incident recalls the
prior one. RAG/memory tests skip cleanly if HF weights unavailable.

## Out of scope (Phase 2)
FastAPI/API + HITL (P3); frontend (P4); LangSmith eval harness / CI gate, Azure deploy,
Docker, DCR/DCE ingestion (P5); GitHub push. Cloud/NVD calls stay behind `MOCK_MODE=false`
and are not required to run.
