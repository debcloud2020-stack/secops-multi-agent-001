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
2. **Real tool integrations** — Azure Sentinel logs; NVD/KEV/EPSS; scanners.
   **DoD:** agents produce findings from real sources behind the `mock_mode` switch.
3. **Agentic RAG** — LlamaIndex + LanceDB retrieval feeding agents.
   **DoD:** retrieval-augmented findings with citations; offline fixtures for tests.
4. **Guardrail + memory + cost + evals** — prompt-injection guardrail, long-term
   memory, cost optimization, eval harness (pytest + LangSmith).
   **DoD:** guardrail blocks documented injection classes; evals gate quality in CI.
5. **Frontend + Azure deploy** — Next.js + shadcn polling UI; containerized deploy.
   **DoD:** UI renders incidents/findings/plan; deployed with managed identity.

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
