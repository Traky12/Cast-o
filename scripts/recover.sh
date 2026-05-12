#!/bin/bash
set -euo pipefail

echo "[recover] Iniciando recuperación de workflows"

for WORKFLOW in "deploy-hetzner-staging.yml" "e2e-first-sale.yml"; do
  echo "[recover] Verificando ${WORKFLOW}"
  LAST_ID=$(gh run list --workflow "$WORKFLOW" --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null || echo "")
  LAST_STATUS=$(gh run list --workflow "$WORKFLOW" --limit 1 --json conclusion -q '.[0].conclusion' 2>/dev/null || echo "unknown")

  if [ "$LAST_STATUS" = "failure" ] && [ -n "$LAST_ID" ]; then
    echo "[recover] Reintentando run ${LAST_ID}"
    gh run rerun "$LAST_ID"
  else
    echo "[recover] Estado ${WORKFLOW}: ${LAST_STATUS}"
  fi
done

HEALTH_URL=${STAGING_HEALTHCHECK_URL:-"https://staging.castuo-system.es/health"}
if curl -fsS --max-time 10 "$HEALTH_URL" >/dev/null; then
  echo "[recover] Sistema recuperado"
else
  echo "[recover] Sistema aún con fallos: endpoint no responde"
  exit 1
fi
