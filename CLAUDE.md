# CLAUDE.md — SecOps Multi-Agent

Agent instructions for this repository. Read this before making changes.

## Project overview
A multi-agent cybersecurity demo. Five specialist agents — **Log Monitor, Threat
Intel, Vuln Scanner, Policy Checker, Incident Response** — are coordinated by a
**supervisor** built in **LangGraph**. The system is fed by Azure Sentinel logs, uses
agentic RAG (LlamaIndex + LanceDB), and adds an eval harness, a prompt-injection
guardrail, long-term memory, and cost optimization. The frontend (Next.js + shadcn)
and Azure deployment come in later phases.

## Scope
- In scope: the agents/graph, RAG, evals, guardrail, memory, cost optimization,
  a Next.js frontend, and Azure deployment — delivered phase by phase.
- **OUT of scope for the entire project: MCP and coding-agents.** Do not add them.

## Architecture summary
See **[PLAN.md](PLAN.md)** in the repo root for the full architecture and the
end-to-end design. At runtime: `START → supervisor → (route) → one agent → supervisor →
… → FINISH → END`, with state carried in `SecOpsState` and an in-memory checkpointer.

## Tech stack + versions
- **Python 3.12**, managed with **uv** (no pip/poetry). macOS dev.
- **LangGraph** + **LangChain core**; **langchain-openai** `ChatOpenAI` against
  **OpenRouter** (`https://openrouter.ai/api/v1`).
- **pydantic** v2 + **pydantic-settings**.
- LLM tiers from env (no hardcoded IDs): `LLM_MODEL_CHEAP` (supervisor/triage),
  `LLM_MODEL_STRONG` (incident-response synthesis).
- Frontend (later): **Next.js + shadcn**, package-managed with **npm**, Node 22.
- Deployment (later): **Azure** (Container Apps + Static Web Apps), managed identity.

## Repo layout
```
backend/        Python package `secops` (primary deliverable)
  secops/       config, llm, state, agents, graph, app(CLI)
  fixtures/     mock incident
  tests/        smoke test
apps/web/       Next.js frontend (placeholder until the frontend phase)
evals/          eval harness (placeholder)
infra/          Azure IaC / Docker (placeholder)
docs/plans/     per-phase implementation plans
.claude/agents/ five project subagents
.claude/skills/ installed skill packs (symlinks into .agents/skills/)
PLAN.md         full architecture + roadmap (source of truth)
```

## Conventions
- **Python:** type hints + `from __future__ import annotations`; ruff for lint
  (blocking); mypy advisory in Phase 1 (`ignore_missing_imports = true`). Keep the
  offline `mock_mode` path working — tests must run with no cloud/LLM creds.
- **TypeScript (later):** strict mode, component-driven, typed backend contracts.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org)
  (`feat:`, `fix:`, `chore:`, …).
- **Branches:** short-lived feature branches off `main`; squash-merge. Phase 1 commits
  are **local only** (no GitHub remote yet).

## How to run locally (mock mode)
```bash
uv python install 3.12        # once
cd backend && uv sync
uv run python -m secops.app run --incident "Critical RCE in gateway"
```
Runs fully offline (LLM stubbed). To use a real model, copy `backend/.env.example` to
`backend/.env`, set `MOCK_MODE=false`, `OPENROUTER_API_KEY`, and the two model IDs.

## How to verify
**Blocking gate (must pass before any commit):**
```bash
cd backend
uv run ruff check .                                              # lint
uv run pytest -q                                                 # tests + smoke
uv run python -m secops.app run --incident "Critical RCE in gateway"   # smoke run
```
**Advisory (non-blocking):** `uv run mypy secops`.

## Secrets policy
- **Never commit secrets.** `.env` is gitignored; only `.env.example` (placeholders) is
  committed. Never hardcode model IDs or API keys in source.
- In the cloud (later), use **managed identity** — no static credentials in images/env.

## Phases & definition of done
1. **Foundation & backend core (mock mode)** — runnable monorepo; LangGraph supervisor
   routes through five agent stubs over mock data, end-to-end, locally.
   **DoD:** the CLI visits all five agents in order and prints findings + a plan
   (offline, also works with a real key); CLAUDE.md, subagents, and both skill packs
   installed; a smoke test asserts five-visit + plan; one clean local commit.
2. **Tools, RAG, and the feature layers** — real (mock-defaulted) tools (Azure
   Monitor/Sentinel KQL detections, NVD/KEV/EPSS enrichment, trivy/pip-audit), agentic
   RAG (LlamaIndex + LanceDB, local HF embeddings), and the guardrail / long-term memory
   / cost-accounting logic that were no-op state fields in Phase 1, all wired into the
   graph (`memory_recall → guardrail → supervisor ⇄ agents → memory_write`).
   **DoD:** with `MOCK_MODE=true` the CLI runs end-to-end and prints findings, a
   priority-sorted `cve_matches` table, similar past incidents, guardrail flags, and a
   cost summary; RAG builds offline; an injected log line is flagged (not obeyed); a
   similar incident recalls the prior one; tool/guardrail/memory/cost/smoke tests pass.
3. **FastAPI API layer** — password middleware + polling endpoints (`/runs`,
   `/runs/{id}`, `/threats`, `/compliance`, `/incidents`) + curated incidents, **plus the
   human-in-the-loop (HITL) approval interrupt and the `POST /runs/{id}/approve` resume
   flow** (LangGraph `interrupt` before the incident-response plan).
   **DoD:** runs start/poll over HTTP behind the password gate; an interrupted run
   resumes via `/approve`.
4. **Frontend** — Next.js + shadcn landing page + polling dashboard (agent rail, findings
   feed, cost panel, similar-incidents, guardrail flags, threats/compliance/history).
   **DoD:** dashboard renders incidents/findings/plan/cost live against the API.
5. **Evals + Azure deploy** — split into two sub-phases:
   - **5a. Evaluation harness (LOCAL, mock-first)** — an offline `evals/` suite over the
     graph: a versioned golden dataset, deterministic + LLM-judge + theme-specific
     evaluators (guardrail catch-rate, memory-recall, cost regression), thresholds set
     against a **measured** baseline, and a **dormant** `.github/workflows/eval.yml` CI
     file (created, not pushed/activated). `langsmith` only (no AgentEvals).
     **DoD:** `cd backend && uv run pytest ../evals -q` runs the golden set, scores every
     evaluator, and asserts thresholds — passing offline (the LLM-judge skips cleanly
     without a key); baseline recorded in `evals/BASELINE.md`; one clean local commit.
   - **5b-1. Functional data-mode + Postgres + Docker (LOCAL)** — make `data_mode` a
     real per-run choice (mock/live/synthetic threaded through state → tools, with
     auto-fallback-to-mock notices), a config-driven Postgres checkpointer
     (`POSTGRES_DSN`; MemorySaver default) with the msgpack serializer fix, and a
     Docker/compose local stack. **DoD:** all three data modes complete locally; Postgres
     checkpointer persists + HITL resumes; backend builds + runs in Docker; verify gate green.
   - **5b-2. Azure deploy via GitHub Actions (deploy-as-code)** — `infra/` Bicep (RG, Log
     Analytics + Sentinel, ACR, Postgres Flexible, Container Apps w/ system-assigned managed
     identity → Log Analytics Reader, Static Web Apps, DCE/DCR custom table) + deploy/teardown
     scripts; GitHub Actions deploy workflows (OIDC, no committed secrets); synthetic ingestion
     + AzureActivity live data; spend cap + teardown runbook; judge baseline. **Authored as
     code and pushed to GitHub; Azure provisioning/deploy is run manually by the owner.**
     **DoD:** deploy workflows + infra committed; manual deploy yields a working SWA + ACA
     app with managed identity (no secrets); eval CI green.

## Installed skills & when to use each
Skill packs `obra/superpowers` and `mattpocock/skills` are installed under
`.claude/skills/` (symlinked from `.agents/skills/`). Useful ones here:
- **writing-plans / executing-plans** — author and execute phase plans (plans live in
  `docs/plans/`).
- **test-driven-development / tdd** — write tests before implementation.
- **verification-before-completion** — run the verify gate before declaring done.
- **systematic-debugging / diagnose** — structured debugging.
- **requesting-code-review / review** — review diffs before committing.
- **using-git-worktrees** — isolate parallel work.
Review any skill before relying on it; they run with full permissions.

## Subagents & roles (`.claude/agents/`)
- **backend-engineer** — Python, LangGraph/LangChain, FastAPI, LlamaIndex + LanceDB.
- **frontend-engineer** — Next.js, shadcn, polling UI.
- **eval-engineer** — pytest, LangSmith, evaluators, CI.
- **azure-infra** — Docker, Container Apps, Static Web Apps, managed identity, deploy.
- **security-reviewer** — prompt-injection/guardrail review, secret hygiene, OWASP LLM.

## Hard guardrails (always)
- **No deploy and no real-data/cloud access without explicit approval.**
- **Respect the spend cap** — keep `max_supervisor_steps` bounded; prefer the cheap
  tier; don't add expensive calls without need.
- **Stay within the current phase** — do not pull later-phase work forward.
- **No GitHub push** until the project owner enables a remote.
- MCP and coding-agents remain out of scope for the whole project.
