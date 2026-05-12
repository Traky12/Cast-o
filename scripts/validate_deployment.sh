#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${CASTUO_NAMESPACE:-castuo-system}"

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

ok() {
  echo "[OK] $*"
}

cmd_exists() {
  command -v "$1" >/dev/null 2>&1
}

cmd_exists kubectl || fail "kubectl no esta instalado"
cmd_exists jq || fail "jq no esta instalado"

pods_json="$(kubectl get pods -n "$NAMESPACE" -o json)"
total_pods="$(echo "$pods_json" | jq '.items | length')"
running_pods="$(echo "$pods_json" | jq '[.items[] | select(.status.phase == "Running")] | length')"

if [[ "$total_pods" -eq 0 ]]; then
  fail "No hay pods en namespace $NAMESPACE"
fi

availability_pct=$(( running_pods * 100 / total_pods ))
if [[ "$availability_pct" -lt 90 ]]; then
  fail "Disponibilidad de pods ${availability_pct}% (<90%)"
fi
ok "Pods running: $running_pods/$total_pods (${availability_pct}%)"

kubectl get hpa -n "$NAMESPACE" >/dev/null
ok "HPA accesible en namespace $NAMESPACE"

if kubectl logs deployment/stac-ingestion -n "$NAMESPACE" --tail=200 | grep -q "ERROR"; then
  fail "Se detectaron errores criticos en logs de stac-ingestion"
fi
ok "Logs de stac-ingestion sin ERROR"

if ! kubectl get svc satellite-api-service -n "$NAMESPACE" >/dev/null 2>&1; then
  fail "No existe service satellite-api-service"
fi
ok "Service satellite-api-service disponible"

echo "[GO] Validacion de despliegue completada"
