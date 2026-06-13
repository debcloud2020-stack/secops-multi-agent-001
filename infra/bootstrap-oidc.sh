#!/usr/bin/env bash
# One-time: create an Entra app registration with GitHub OIDC federated credentials so the
# deploy workflows authenticate to Azure WITHOUT a stored client secret, grant it
# Contributor on the resource group, and push the three non-secret IDs as GitHub secrets.
#
#   ./infra/bootstrap-oidc.sh
#
# Requires: az login (as an owner who can create app registrations + assign roles), gh auth.
set -euo pipefail

RG="${RG:-secops-rg}"
APP_NAME="${APP_NAME:-secops-gha-oidc}"
REPO="${REPO:-debcloud2020-stack/secops-multi-agent-001}"
SUB_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"

echo ">> Creating app registration $APP_NAME"
APP_ID="$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)"
az ad sp create --id "$APP_ID" --output none || true

echo ">> Federated credential for main + pull_request (repo $REPO)"
for SUBJECT in "repo:${REPO}:ref:refs/heads/main" "repo:${REPO}:pull_request"; do
  NAME="gha-$(echo "$SUBJECT" | tr -c 'a-zA-Z0-9' '-')"
  az ad app federated-credential create --id "$APP_ID" --parameters "{
    \"name\": \"${NAME}\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"${SUBJECT}\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }" --output none
done

echo ">> Granting Contributor on $RG (create the RG first if it doesn't exist)"
az role assignment create --assignee "$APP_ID" --role Contributor \
  --scope "/subscriptions/${SUB_ID}/resourceGroups/${RG}" --output none

echo ">> Pushing GitHub repo secrets (IDs are not sensitive, but kept as secrets)"
gh secret set AZURE_CLIENT_ID --repo "$REPO" --body "$APP_ID"
gh secret set AZURE_TENANT_ID --repo "$REPO" --body "$TENANT_ID"
gh secret set AZURE_SUBSCRIPTION_ID --repo "$REPO" --body "$SUB_ID"

cat <<NEXT

OIDC ready. Still to set (see infra/README.md):
  gh secret set AZURE_STATIC_WEB_APPS_TOKEN --repo $REPO --body <swa deploy token>
  gh variable set ACR_NAME --repo $REPO --body <acrName output>
  gh variable set BACKEND_APP_NAME --repo $REPO --body <backendAppName output>
  gh variable set RESOURCE_GROUP --repo $REPO --body $RG
  gh variable set BACKEND_URL --repo $REPO --body <backendUrl output>
NEXT
