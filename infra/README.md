# infra — Azure deploy (Phase 5b-2)

Deploy-as-code for the SecOps demo. **You run the Azure steps manually** (this spends real
money). Everything here is committed; nothing is auto-provisioned. Region default: `eastus`.

> **Spend first, deploy second.** Set a budget alert and plan to tear down after each demo —
> see [Spend cap](#spend-cap--teardown). Idle baseline is ~$20–30/mo (Postgres + ACR);
> `teardown.sh` zeroes it.

## What gets created (`main.bicep`, resource-group scoped)
Log Analytics workspace + **Microsoft Sentinel**, **ACR** (Basic), **Postgres Flexible
Server** (Burstable B1ms) + db, **Container Apps** env + the backend app (system-assigned
**managed identity** → AcrPull + Log Analytics Reader; secrets as Container App secrets),
**Static Web App** (Free), and the synthetic **Logs-Ingestion** plumbing (DCE + DCR +
`SecOpsSynthetic_CL` table) via `ingestion.bicep`.

## Prerequisites
`az` (logged in as an owner who can create app registrations + assign roles), `gh` (logged
in), Docker not required. The repo: `debcloud2020-stack/secops-multi-agent-001`.

## One-time: GitHub → Azure OIDC (no stored client secret)
```bash
az login
az group create -n secops-rg -l eastus   # bootstrap-oidc grants Contributor here
./infra/bootstrap-oidc.sh
```
This creates the app registration + federated credentials (main + PRs), grants Contributor
on the RG, and pushes `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID` as repo
secrets.

## Provision
```bash
export DEMO_PASSWORD='<demo password>'
export POSTGRES_ADMIN_PASSWORD='<strong password>'
export OPENROUTER_API_KEY='<optional>'        # empty = offline LLM stub in the cloud too
./infra/deploy.sh                              # idempotent; prints outputs
```
Note the outputs: `acrName`, `backendUrl`, `backendAppName`, `staticWebAppName`,
`dceLogsIngestionEndpoint`, `dcrImmutableId`.

## Wire up CI + deploy the apps
```bash
# Secrets/vars the workflows need (the AZURE_* IDs are already set by bootstrap-oidc):
gh secret   set AZURE_STATIC_WEB_APPS_TOKEN --repo <repo> --body "$(az staticwebapp secrets list -n <staticWebAppName> --query properties.apiKey -o tsv)"
gh variable set ACR_NAME         --repo <repo> --body <acrName>
gh variable set RESOURCE_GROUP   --repo <repo> --body secops-rg
gh variable set BACKEND_APP_NAME --repo <repo> --body <backendAppName>
gh variable set BACKEND_URL      --repo <repo> --body <backendUrl>

gh workflow run deploy-backend.yml   --repo <repo>   # ACR build → Container Apps
gh workflow run deploy-frontend.yml  --repo <repo>   # static export (API URL inlined) → SWA
```
Then point CORS at the SWA origin (re-run `deploy.sh` with `CORS_ORIGINS=<swa url>` or
`az containerapp update -n <backendAppName> -g secops-rg --set-env-vars CORS_ORIGINS=<swa url>`).

## Synthetic data (data_mode = "synthetic")
```bash
pip install azure-monitor-ingestion azure-identity
export DCE_ENDPOINT=<dceLogsIngestionEndpoint> DCR_IMMUTABLE_ID=<dcrImmutableId> STREAM_NAME=Custom-SecOpsSynthetic
python infra/ingest_synthetic.py
```
`live` mode uses **AzureActivity** (free, no Entra P1); rich sign-in demos come from the
synthetic table above.

## Secrets — what lives where (never committed)
| Secret | Where it lives | Used by |
|---|---|---|
| `AZURE_CLIENT_ID` / `TENANT_ID` / `SUBSCRIPTION_ID` | GitHub repo **secrets** | `azure/login` OIDC in both deploy workflows |
| `AZURE_STATIC_WEB_APPS_TOKEN` | GitHub repo **secret** | `deploy-frontend` → SWA upload |
| `DEMO_PASSWORD` | Container App **secret** (deploy param) | API password gate |
| Postgres password → `POSTGRES_DSN` | Container App **secret** (built in Bicep) | LangGraph Postgres checkpointer |
| `OPENROUTER_API_KEY` | Container App **secret** (deploy param) | live LLM tier + the judge baseline |
| `ACR_NAME` / `RESOURCE_GROUP` / `BACKEND_APP_NAME` / `BACKEND_URL` | GitHub repo **variables** (not secret) | deploy workflows |

## Spend cap + teardown
- **Budget alert** (optional, subscription-scoped): `az deployment sub create -l eastus -f infra/budget.bicep -p amount=25 contactEmails='["you@example.com"]'`. Alerts only — it does not hard-stop.
- **Pause:** `az containerapp update -n <backendAppName> -g secops-rg --min-replicas 0` and stop the Postgres server.
- **Zero the bill:** `./infra/teardown.sh` (deletes the resource group).

## Notes
- `main.bicep`'s container image defaults to a public placeholder so the **first** deploy
  succeeds before any image exists in ACR; `deploy-backend` then pushes + sets the real image.
- Bicep here is authored, not compiled in CI — validate locally with `az bicep build -f infra/main.bicep` before your first deploy.
- The judge baseline (`plan_quality`) is recorded after deploy when a key is available — see `evals/BASELINE.md`.
