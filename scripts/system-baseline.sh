#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env"
CHECK_CLUSTER=0
CHECK_ENDPOINTS=0

usage() {
  cat <<'EOF'
Uso: scripts/system-baseline.sh [opciones]

Opciones:
  --env-file <ruta>      Archivo env (default: .env)
  --check-cluster        Incluye checks kubectl contra cluster real
  --check-endpoints      Incluye checks de endpoints externos del hub
  -h, --help             Mostrar ayuda

Salida:
  - GO: 0 errores
  - NO-GO: 1+ errores
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --check-cluster)
      CHECK_CLUSTER=1
      shift
      ;;
    --check-endpoints)
      CHECK_ENDPOINTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Parametro no reconocido: $1" >&2
      exit 2
      ;;
  esac
done

errors=0

run_step() {
  local label="$1"
  shift
  echo
  echo "[STEP] $label"
  if "$@"; then
    echo "[OK]   $label"
  else
    echo "[FAIL] $label"
    errors=$((errors + 1))
  fi
}

echo "== CASTUO BASELINE: coherencia + seguridad + optimizacion =="

run_step "Secretos requeridos" bash scripts/validate_secrets.sh

if [[ "$CHECK_ENDPOINTS" -eq 1 ]]; then
  run_step "Conectividad hub (strict + endpoints)" \
    bash scripts/validate_hub_connectivity.sh --env-file "$ENV_FILE" --strict --check-endpoints
else
  run_step "Conectividad hub (strict)" \
    bash scripts/validate_hub_connectivity.sh --env-file "$ENV_FILE" --strict
fi

run_step "Pruebas funcionales core" make test-all
run_step "Workflow n8n valido" make validate-n8n

run_step "Compose microservicios valido" \
  bash -lc 'POSTGRES_PASSWORD=test N8N_BASIC_AUTH_USER=admin N8N_BASIC_AUTH_PASSWORD=test docker compose -f docker-compose.microservices.yml config >/dev/null'
run_step "Compose satelital valido" \
  docker compose -f docker-compose.satellite.yml config >/dev/null

run_step "Kubernetes core sintacticamente valido" \
  docker run --rm -v "$PWD:/workdir" -w /workdir ghcr.io/yannh/kubeconform:latest -strict -summary \
    k8s/namespace.yaml k8s/configmap.yaml k8s/secrets.example.yaml k8s/pvc.yaml \
    k8s/deployment.yaml k8s/service.yaml k8s/ingress.yaml k8s/hpa.yaml k8s/networkpolicy.yaml

run_step "Kubernetes satelital sintacticamente valido" \
  docker run --rm -v "$PWD:/workdir" -w /workdir ghcr.io/yannh/kubeconform:latest -strict -summary \
    k8s/satellite/configmap.yaml k8s/satellite/deployment.yaml k8s/satellite/service.yaml k8s/satellite/hpa.yaml

run_step "Terraform valido" \
  docker run --rm -v "$PWD/hetzner_infra:/data" -w /data hashicorp/terraform:1.8.5 validate

if [[ "$CHECK_CLUSTER" -eq 1 ]]; then
  run_step "Cluster accesible (kubectl get nodes)" kubectl get nodes
  run_step "K8s dry-run server" kubectl apply --dry-run=server -f k8s/
fi

run_step "Hardening local" make agent-hardening
run_step "Reconcile dry-run con politica por rama" make reconcile-check

echo
if [[ "$errors" -eq 0 ]]; then
  echo "[GO] Baseline completado sin errores"
  exit 0
fi

echo "[NO-GO] Baseline con $errors error(es)"
exit 1
