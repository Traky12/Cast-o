#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${CASTUO_NAMESPACE:-castuo-system}"
SKIP_BUILD="${SKIP_BUILD:-0}"

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

ok() {
  echo "[OK] $*"
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Comando no disponible: $1"
}

need_cmd kubectl
need_cmd bash

if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi

bash scripts/validate_secrets.sh
ok "Preflight de secretos completado"

bash scripts/configure-kubectl-hetzner.sh --from-env-b64 || bash scripts/configure-kubectl-hetzner.sh --from-ssh
ok "kubectl configurado para Hetzner"

if [[ "$SKIP_BUILD" != "1" ]]; then
  need_cmd docker-compose
  docker-compose -f docker-compose.satellite.yml build
  docker-compose -f docker-compose.satellite.yml push
  ok "Imagenes satelitales build+push completadas"
fi

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/satellite/
kubectl apply -f k8s/storage/
kubectl apply -f k8s/blockchain/
kubectl apply -f k8s/kafka/
kubectl apply -f k8s/api/
ok "Manifests aplicados"

CASTUO_NAMESPACE="$NAMESPACE" bash scripts/validate_deployment.sh
ok "Validacion final GO"

echo "[DONE] Despliegue satelital completado en namespace ${NAMESPACE}"
