#!/usr/bin/env bash
# Provision the SecOps Azure stack (idempotent). Run MANUALLY — this spends money.
#
#   export DEMO_PASSWORD=... POSTGRES_ADMIN_PASSWORD=... [OPENROUTER_API_KEY=...]
#   ./infra/deploy.sh
#
# Re-runnable: `az deployment group create` is a declarative upsert. Tear down with
# ./infra/teardown.sh (deletes the whole resource group). Set a budget first — see README.
set -euo pipefail

RG="${RG:-secops-rg}"
LOCATION="${LOCATION:-eastus}"
PREFIX="${PREFIX:-secops}"

: "${DEMO_PASSWORD:?set DEMO_PASSWORD}"
: "${POSTGRES_ADMIN_PASSWORD:?set POSTGRES_ADMIN_PASSWORD}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"

echo ">> Resource group $RG ($LOCATION)"
az group create --name "$RG" --location "$LOCATION" --output none

echo ">> Deploying main.bicep (this can take ~10-15 min the first time)"
az deployment group create \
  --resource-group "$RG" \
  --template-file "$(dirname "$0")/main.bicep" \
  --parameters "$(dirname "$0")/main.parameters.json" \
  --parameters \
      prefix="$PREFIX" \
      location="$LOCATION" \
      corsOrigins="$CORS_ORIGINS" \
      demoPassword="$DEMO_PASSWORD" \
      postgresAdminPassword="$POSTGRES_ADMIN_PASSWORD" \
      openRouterApiKey="$OPENROUTER_API_KEY" \
  --output none

echo ">> Outputs:"
az deployment group show --resource-group "$RG" --name main \
  --query properties.outputs --output json

cat <<'NEXT'

Next steps (see infra/README.md):
  1. Note the outputs above (acrName, backendUrl, staticWebAppName, dce/dcr ids).
  2. Set the GitHub repo secrets/vars, then run the deploy workflows to build+push the
     real backend image and the frontend (built with NEXT_PUBLIC_API_URL=<backendUrl>).
  3. Re-run deploy with corsOrigins=<staticWebApp URL> (or `az containerapp update`) so
     the API allows the SWA origin.
  4. Push synthetic data:  python infra/ingest_synthetic.py
NEXT
