# Phase 1 — Foundation & backend core (mock mode)

Status: **implemented**. This is the as-built record of Phase 1.

## Context
Greenfield monorepo for a multi-agent cybersecurity demo. Phase 1 delivers only the
runnable skeleton: a LangGraph supervisor that routes through five agent **stubs** over
**mock** data, end-to-end, locally, with the LLM stubbed (and optionally driven by a
real OpenRouter key). No real tools, RAG, API, frontend, cloud, or GitHub push.

## Decisions
- `secops/` lives at `backend/secops/`; commands run from `backend/`.
- Mock-mode routing is **deterministic** (`AGENT_ORDER`) so all five agents are always
  visited; the supervisor consults the cheap model for a triage note but order is
  authoritative. `max_supervisor_steps` is a hard loop guard.
- LLM stub = `OfflineChatModel(BaseChatModel)` in `secops/llm.py`, auto-selected when
  `mock_mode` is true OR no `OPENROUTER_API_KEY` is set; importable by tests.
- `PLAN.md` is provided by the project owner (repo root) and used verbatim; this phase
  does **not** generate or modify it. CLAUDE.md points to it.
- Type-checking is **advisory** in Phase 1 (mypy `ignore_missing_imports = true`); the
  blocking gate is **ruff + pytest + smoke run**.
- Placeholders `apps/web/`, `evals/`, `infra/` each get a `README.md`.
- Model IDs stay as env placeholders in `backend/.env.example`.

## What was built
- **Scaffold:** `backend/`, `apps/web/`, `evals/`, `infra/`, `docs/plans/`,
  `.claude/agents/`; root `.gitignore`; nested `git init` (independent of the home repo).
- **Backend `secops/`:** `config.py` (pydantic-settings), `llm.py` (OpenRouter
  factories + `OfflineChatModel`), `state.py` (`SecOpsState` + `Incident`/`Finding`/
  `CVEMatch`, incl. no-op `similar_past`/`guardrail_flags`/`cost`), `agents.py`
  (supervisor + five mock nodes + `route()`; `incident_response` uses the strong tier),
  `graph.py` (`StateGraph` + `MemorySaver`), `app.py` (CLI), `fixtures/mock_incident.json`,
  `tests/test_smoke.py`.
- **Skills:** `obra/superpowers` + `mattpocock/skills` installed under `.agents/skills/`,
  symlinked into `.claude/skills/`.
- **Docs/config:** root `CLAUDE.md`; five subagents in `.claude/agents/`.

## How to run / verify
```bash
uv python install 3.12 && cd backend && uv sync
uv run python -m secops.app run --incident "Critical RCE in gateway"   # smoke run
uv run ruff check .        # blocking
uv run pytest -q           # blocking (smoke test)
uv run mypy secops         # advisory
```

## Definition of done — met
- CLI visits all five agents in order and prints findings + a response plan (offline;
  also works with a real key).
- CLAUDE.md, five subagents, and both skill packs installed.
- Smoke pytest asserts five-visit + plan.
- One clean **local** git commit; no GitHub push.

## Out of scope (Phase 1)
Real tool integrations; RAG/LlamaIndex/LanceDB; guardrail/memory/cost **logic** (fields
are no-ops); FastAPI/API; frontend beyond the placeholder; Azure/Docker/cloud; GitHub
push; LangSmith/eval wiring.
