#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env"
RUN_CLUSTER=1
RUN_ENDPOINTS=1

usage() {
  cat <<'EOF'
Uso: scripts/go-total.sh [opciones]

Opciones:
  --env-file <ruta>       Archivo .env para validacion hub (default: .env)
  --skip-cluster          Omitir validaciones kubectl contra API server real
  --skip-endpoints        Omitir health-check de endpoints externos en hub
  -h, --help              Mostrar ayuda

Salida:
  - GO total: todas las fases criticas completadas.
  - NO-GO: falla alguna fase (se indica causa y accion recomendada).
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --skip-cluster)
      RUN_CLUSTER=0
      shift
      ;;
    --skip-endpoints)
      RUN_ENDPOINTS=0
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

phase() {
  echo
  echo "============================================================"
  echo "[PHASE] $1"
  echo "============================================================"
}

run() {
  local title="$1"
  shift
  echo "[RUN] $title"
  if "$@"; then
    echo "[OK]  $title"
  else
    echo "[ERROR] $title"
    return 1
  fi
}

phase "1) Secretos base"
run "Validar secretos locales" bash scripts/validate_secrets.sh

phase "2) Calidad y artefactos"
run "Tests principales (44)" make test-all
run "Workflow n8n JSON" make validate-n8n
run "Compose microservicios" bash -lc 'POSTGRES_PASSWORD=test N8N_BASIC_AUTH_USER=admin N8N_BASIC_AUTH_PASSWORD=test docker compose -f docker-compose.microservices.yml config >/dev/null'

phase "3) Infra sintactica"
run "Kubernetes offline (kubeconform)" docker run --rm -v "$PWD:/workdir" -w /workdir ghcr.io/yannh/kubeconform:latest -strict -summary k8s/namespace.yaml k8s/configmap.yaml k8s/secrets.example.yaml k8s/pvc.yaml k8s/deployment.yaml k8s/service.yaml k8s/ingress.yaml k8s/hpa.yaml k8s/networkpolicy.yaml
run "Terraform validate" docker run --rm -v "$PWD/hetzner_infra:/data" -w /data hashicorp/terraform:1.8.5 validate

phase "4) Conectividad hub"
if [[ "$RUN_ENDPOINTS" -eq 1 ]]; then
  run "Hub connectivity strict + endpoints" bash scripts/validate_hub_connectivity.sh --env-file "$ENV_FILE" --strict --check-endpoints
else
  run "Hub connectivity strict" bash scripts/validate_hub_connectivity.sh --env-file "$ENV_FILE" --strict
fi

if [[ "$RUN_CLUSTER" -eq 1 ]]; then
  phase "5) Cluster real"
  run "kubectl get nodes" kubectl get nodes
  run "kubectl apply dry-run server" kubectl apply --dry-run=server -f k8s/
fi

phase "6) Hardening y drift"
run "Agent hardening" make agent-hardening
run "Reconcile dry-run" make reconcile-check

echo
echo "[GO] Excelencia operativa total validada"
