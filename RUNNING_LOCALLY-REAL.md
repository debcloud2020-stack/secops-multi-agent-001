# Running locally against REAL integrations

Run the whole system with **no mock**: real OpenRouter LLM, real NVD/KEV/EPSS, real
trivy/pip-audit, and real Azure Log Analytics (live **AzureActivity** + **synthetic** custom
table). Any time a real source is unavailable the run **falls back to mock with a loud
`data_notices` entry** (visible as an amber banner in the dashboard) — so you always know.

> **Secrets never get committed.** `backend/.env` is gitignored; only `.env.example`
> (placeholders) is tracked. CI stays offline (`MOCK_MODE=true`).

## 1. Prerequisites
- `az login` as an identity with **read** on the workspace and **Monitoring Metrics
  Publisher** on the DCR (for seeding). `DefaultAzureCredential` uses this session.
- `trivy` and `pip-audit` on PATH for the real scanner path (`brew install trivy`,
  `uv tool install pip-audit` or `pipx install pip-audit`).
- Your OpenRouter API key + current model ids.

## 2. `backend/.env` (create it — gitignored)
```dotenv
MOCK_MODE=false
AZURE_WORKSPACE_ID=***REMOVED***
DCE_ENDPOINT=***REMOVED***
DCR_IMMUTABLE_ID=***REMOVED***
DCR_STREAM_NAME=Custom-SecOpsSynthetic_CL
OPENROUTER_API_KEY=sk-or-...
LLM_MODEL_CHEAP=<cheap model id>
LLM_MODEL_STRONG=<strong model id>
DEMO_PASSWORD=changeme
# optional: POSTGRES_DSN=postgresql://...
```
Confirm it's ignored: `git check-ignore backend/.env` prints the path.

## 3. Install + seed synthetic data
```bash
cd backend && uv sync                                    # picks up azure-monitor-ingestion
uv run python ../scripts/seed_synthetic.py --dry-run     # preview 10 rows (no upload)
uv run python ../scripts/seed_synthetic.py               # uploads ~10 incidents to SecOpsSynthetic_CL
```
Ingestion takes a few minutes to land. Confirm in the portal / a KQL query:
`SecOpsSynthetic_CL | where TimeGenerated > ago(1d) | count`.

## 4. Start the app
```bash
# backend (reads backend/.env → MOCK_MODE=false)
cd backend && uv run uvicorn secops.server:app --port 8000
# frontend (separate terminal)
cd apps/web && npm run dev
```
Open http://localhost:3000 → dashboard → password `changeme`.

## 5. Run an incident in LIVE and SYNTHETIC
Pick an incident, set the toggle to **Live** (then **Synthetic**), Run.

**It used REAL data when:**
- **No amber "Fell back to mock data" banner** (and `data_notices` is empty in `GET /runs/{id}`).
- **threat_intel** shows **CVE-2021-44228** (Log4Shell) with real CVSS 10.0, `KEV=True`, a real EPSS.
- **vuln_scanner** lists real CVEs from `trivy fs` on the repo.
- **log_monitor** (Live) reflects real **AzureActivity** rows; (Synthetic) reflects the seeded rows.
- **LLM**: the response plan's `[synthesis]` is real model prose (not `[offline-stub:...]`).

## 6. Per-integration spot checks (CLI)
```bash
cd backend
# Real NVD/KEV/EPSS (Log4Shell):
uv run python -c "from secops.tools.threat_intel import enrich_cve; print(enrich_cve('CVE-2021-44228','live'))"
# Real scanners:
trivy fs --quiet --format json . | head -c 300 ; pip-audit --format json | head -c 300
# Real live query (AzureActivity) + synthetic table:
uv run python -c "from secops.tools.azure_logs import run_detection as r; print(len(r('azure_activity','live')),'activity rows')"
uv run python -c "from secops.tools.azure_logs import run_detection as r; print(len(r('failed_signins_burst','synthetic')),'synthetic rows')"
```
A non-empty result with **no** printed fallback warning means real. If you see a
`data_notices` entry like `log_monitor: 'live' source unavailable (...)`, the real source
failed (check `az login`, RBAC, region) — it's loud on purpose.

## Notes
- Embeddings (RAG/memory) stay **local** by design — not an external integration.
- `data_mode=mock` always works offline (fixtures) and is the default + what CI runs.
