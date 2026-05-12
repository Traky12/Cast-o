#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CASTÚO-SYSTEM™ v3.1 — Despliegue manual en Kubernetes (Hetzner)
#
# Uso:
#   ./scripts/kubectl-deploy.sh               # aplica todos los manifests
#   ./scripts/kubectl-deploy.sh --check       # solo verifica estado
#   ./scripts/kubectl-deploy.sh --rollback    # rollback del Deployment
#
# Pre-requisitos:
#   - kubectl configurado con el cluster Hetzner (~/.kube/config o KUBECONFIG)
#   - k8s/secret.yaml creado manualmente (NO está en git)
#   - Cert-Manager instalado en el cluster
#   - ingress-nginx instalado en el cluster
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

NS="castuo-system"
K8S_DIR="$(cd "$(dirname "$0")/.." && pwd)/k8s"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

ok()   { echo -e "${GREEN}  ✓${NC} $1"; }
err()  { echo -e "${RED}  ✗${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}  ⚠${NC} $1"; }
info() { echo -e "    $1"; }

# ── Modo rollback ─────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--rollback" ]]; then
    echo "⏮  Rolling back castuo-api deployment..."
    kubectl rollout undo deployment/castuo-api -n "$NS"
    kubectl rollout status deployment/castuo-api -n "$NS" --timeout=90s
    ok "Rollback completado"
    exit 0
fi

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  CASTÚO Kubernetes Deploy — namespace: $NS     ║"
echo "╚═══════════════════════════════════════════════════════╝"

# ── Verificar kubectl ─────────────────────────────────────────────────────────
command -v kubectl &>/dev/null || err "kubectl no encontrado en PATH"
kubectl cluster-info &>/dev/null || err "No se puede conectar al cluster. Revisa KUBECONFIG."
ok "Conexión al cluster OK"

# ── Modo check ────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--check" ]]; then
    echo ""
    echo "── Estado actual ────────────────────────────────────────"
    kubectl get pods       -n "$NS" -l app=castuo-api 2>/dev/null || warn "Namespace $NS no encontrado"
    kubectl get services   -n "$NS" -l app=castuo-api 2>/dev/null || true
    kubectl get ingress     -n "$NS" 2>/dev/null || true
    kubectl get hpa        -n "$NS" 2>/dev/null || true
    echo ""
    kubectl top pods -n "$NS" -l app=castuo-api 2>/dev/null || warn "metrics-server no disponible"
    exit 0
fi

# ── Verificar que k8s/secret.yaml existe ─────────────────────────────────────
if [[ ! -f "$K8S_DIR/secret.yaml" ]]; then
    warn "k8s/secret.yaml no encontrado."
    echo "  Copia y edita el ejemplo:"
    echo "  cp k8s/secret.yaml.example k8s/secret.yaml"
    echo "  # Rellena los valores base64 (ver comentarios en el fichero)"
    echo ""
    read -rp "  ¿Continuar sin secret.yaml? (los secretos se leerán de Vault si está configurado) [y/N] " yn
    [[ "$yn" == "y" || "$yn" == "Y" ]] || exit 1
fi

# ── Aplicar manifests ─────────────────────────────────────────────────────────
echo ""
echo "── Aplicando manifests en namespace: $NS ────────────────"

kubectl apply -f "$K8S_DIR/namespace.yaml"
ok "Namespace"

kubectl apply -f "$K8S_DIR/configmap.yaml"   -n "$NS"
ok "ConfigMap"

if [[ -f "$K8S_DIR/secret.yaml" ]]; then
    kubectl apply -f "$K8S_DIR/secret.yaml" -n "$NS"
    ok "Secret"
else
    warn "secret.yaml omitido — asegúrate de que castuo-secrets existe en el cluster"
fi

kubectl apply -f "$K8S_DIR/deployment.yaml" -n "$NS"
ok "Deployment + ServiceAccount + PVC"

kubectl apply -f "$K8S_DIR/service.yaml"    -n "$NS"
ok "Service + HPA"

kubectl apply -f "$K8S_DIR/ingress.yaml"    -n "$NS"
ok "Ingress + ConfigMap de entorno"

# ── Esperar rollout ───────────────────────────────────────────────────────────
echo ""
echo "── Esperando rollout ────────────────────────────────────"
kubectl rollout status deployment/castuo-api -n "$NS" --timeout=120s
ok "Deployment listo"

# ── Estado final ──────────────────────────────────────────────────────────────
echo ""
echo "── Estado final ─────────────────────────────────────────"
kubectl get pods     -n "$NS" -l app=castuo-api
echo ""
kubectl get services -n "$NS" -l app=castuo-api
echo ""
kubectl get ingress  -n "$NS"

# ── Healthcheck ───────────────────────────────────────────────────────────────
echo ""
echo "── Healthcheck via Ingress ──────────────────────────────"
sleep 5
HTTP=$(curl -sf -o /dev/null -w "%{http_code}" \
    "https://api.castuo-system.cloud/health" 2>/dev/null || echo "000")
if [[ "$HTTP" == "200" ]]; then
    ok "https://api.castuo-system.cloud/health → HTTP 200"
else
    warn "Health check devolvió HTTP $HTTP (DNS puede tardar en propagar)"
fi

echo ""
ok "Despliegue completado — namespace $NS"
echo "  Logs:       kubectl logs -f -n $NS -l app=castuo-api"
echo "  Escalar:    kubectl scale deployment/castuo-api -n $NS --replicas=3"
echo "  Rollback:   $0 --rollback"
echo "  Grafana:    kubectl port-forward -n monitoring svc/grafana 3000:3000"
