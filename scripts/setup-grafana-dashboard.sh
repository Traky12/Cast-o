#!/bin/bash
# Importa el dashboard AEMPS/Cannabis a Grafana (usando Grafana HTTP API).
#
# Requiere:
#   - GRAFANA_URL (ej: http://localhost:3000)
#   - GRAFANA_API_KEY
#   - jq
#
# Dashboard:
#   castu-monitoring/grafana/dashboards/aemps-cannabis-trials.json

set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_API_KEY="${GRAFANA_API_KEY:-}"
DASHBOARD_FILE="${DASHBOARD_FILE:-castu-monitoring/grafana/dashboards/aemps-cannabis-trials.json}"
FOLDER_ID="${FOLDER_ID:-0}"

if [[ -z "${GRAFANA_API_KEY}" ]]; then
  echo "GRAFANA_API_KEY no definida" >&2
  exit 1
fi

if [[ ! -f "${DASHBOARD_FILE}" ]]; then
  echo "No existe DASHBOARD_FILE: ${DASHBOARD_FILE}" >&2
  exit 1
fi

DASHBOARD_JSON="$(cat "${DASHBOARD_FILE}" | jq -c)"

curl -sS -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -d "{
    \"dashboard\": ${DASHBOARD_JSON},
    \"folderId\": ${FOLDER_ID},
    \"overwrite\": true
  }" \
  "${GRAFANA_URL}/api/dashboards/import" >/dev/null

echo "Dashboard importado: ${DASHBOARD_FILE}"

