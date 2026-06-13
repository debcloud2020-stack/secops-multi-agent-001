#!/usr/bin/env bash
# Tear down the entire SecOps stack by deleting the resource group. Run after a demo to
# stop all spend. (To merely pause: `az containerapp update --min-replicas 0` + stop the
# Postgres server; full delete is the surest way to zero the bill.)
set -euo pipefail

RG="${RG:-secops-rg}"

read -r -p "Delete resource group '$RG' and ALL its resources? [y/N] " ans
[[ "$ans" == "y" || "$ans" == "Y" ]] || { echo "aborted"; exit 1; }

echo ">> Deleting $RG (runs in the background)…"
az group delete --name "$RG" --yes --no-wait
echo ">> Submitted. Verify with: az group exists --name $RG"
