#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-castuo-system}"
STAGING_NAMESPACE="${STAGING_NAMESPACE:-castuo-staging}"
API_URL="${API_URL:-http://api.castuo-system.cloud}"

if ! NAMESPACE="${NAMESPACE}" STAGING_NAMESPACE="${STAGING_NAMESPACE}" API_URL="${API_URL}" ./hardening_checklist.sh; then
  echo "❌ Hardening falló"
  exit 1
fi

if ! ./setup_timescale_ha.sh "${NAMESPACE}"; then
  rc=$?
  echo "❌ Setup de Timescale falló (rc=${rc})"
  exit 1
fi

if ! python3 ./scripts/test_e2e.py; then
  rc=$?
  echo "❌ Pruebas E2E fallaron (rc=${rc})"
  exit 1
fi

if ! kubectl port-forward svc/prometheus 9090:9090 -n monitoring >/tmp/castuo-prometheus-pf.log 2>&1 &
then
  echo "❌ No se pudo iniciar port-forward de Prometheus"
  exit 1
fi
PF_PID=$!
trap 'kill ${PF_PID} >/dev/null 2>&1 || true' EXIT
sleep 5
if ! curl -fsS "http://localhost:9090/api/v1/query?query=up" | grep -q '"status":"success"'; then
  echo "❌ Métricas no disponibles"
  exit 1
fi

echo "✅ Todas las validaciones pasaron"
exit 0
