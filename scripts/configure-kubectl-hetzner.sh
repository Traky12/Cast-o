#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CASTÚO-SYSTEM™ v3.1 — Configurar kubectl para Hetzner Kubernetes
#
# Uso:
#   export HETZNER_KUBECONFIG_B64="$(cat ~/.kube/hetzner.yaml | base64)"
#   ./scripts/configure-kubectl-hetzner.sh
#
# O con fichero kubeconfig existente:
#   ./scripts/configure-kubectl-hetzner.sh --kubeconfig ~/.kube/hetzner.yaml
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓${NC} $1"; }
err()  { echo -e "${RED}  ✗${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}  ⚠${NC} $1"; }

KUBECONFIG_FILE=""
CONTEXT_NAME="castuo-hetzner"

for arg in "$@"; do
    case "$arg" in
        --kubeconfig=*) KUBECONFIG_FILE="${arg#*=}" ;;
        --kubeconfig)   KUBECONFIG_FILE="${2:-}"; shift ;;
        --context=*)    CONTEXT_NAME="${arg#*=}" ;;
    esac
done

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  CASTÚO — Configurar kubectl (Hetzner)                ║"
echo "╚═══════════════════════════════════════════════════════╝"

mkdir -p ~/.kube

# ── Opción A: Variable de entorno base64 ─────────────────────────────────────
if [[ -n "${HETZNER_KUBECONFIG_B64:-}" ]]; then
    echo "  Fuente: HETZNER_KUBECONFIG_B64 (variable de entorno)"
    echo "$HETZNER_KUBECONFIG_B64" | base64 -d > ~/.kube/castuo-hetzner.yaml
    chmod 600 ~/.kube/castuo-hetzner.yaml
    KUBECONFIG_FILE=~/.kube/castuo-hetzner.yaml
    ok "Kubeconfig decodificado → ~/.kube/castuo-hetzner.yaml"

# ── Opción B: Fichero kubeconfig existente ────────────────────────────────────
elif [[ -n "$KUBECONFIG_FILE" && -f "$KUBECONFIG_FILE" ]]; then
    echo "  Fuente: $KUBECONFIG_FILE"

# ── Opción C: hcloud CLI ──────────────────────────────────────────────────────
elif command -v hcloud &>/dev/null && [[ -n "${HETZNER_API_KEY:-}" ]]; then
    echo "  Fuente: hcloud CLI"
    export HCLOUD_TOKEN="$HETZNER_API_KEY"

    # Listar clusters disponibles
    CLUSTERS=$(hcloud k8s cluster list -o json 2>/dev/null || echo "[]")
    N=$(echo "$CLUSTERS" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo 0)

    if [[ "$N" -eq 0 ]]; then
        err "No se encontraron clusters Hetzner Kubernetes. Crea uno primero."
    elif [[ "$N" -eq 1 ]]; then
        CLUSTER_NAME=$(echo "$CLUSTERS" | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['name'])")
        echo "  Cluster: $CLUSTER_NAME"
        hcloud k8s cluster get-kubeconfig "$CLUSTER_NAME" > ~/.kube/castuo-hetzner.yaml
        chmod 600 ~/.kube/castuo-hetzner.yaml
        KUBECONFIG_FILE=~/.kube/castuo-hetzner.yaml
        ok "Kubeconfig descargado → ~/.kube/castuo-hetzner.yaml"
    else
        echo "  Clusters disponibles:"
        echo "$CLUSTERS" | python3 -c "import json,sys; [print(f'    {c[\"name\"]}') for c in json.load(sys.stdin)]"
        err "Múltiples clusters. Usa: hcloud k8s cluster get-kubeconfig <nombre> > ~/.kube/castuo-hetzner.yaml"
    fi

else
    echo ""
    echo "  No se encontró configuración de acceso. Opciones:"
    echo ""
    echo "  1. Variable de entorno (recomendado para CI/CD):"
    echo "     export HETZNER_KUBECONFIG_B64=\"\$(cat ~/.kube/config | base64)\""
    echo "     ./scripts/configure-kubectl-hetzner.sh"
    echo ""
    echo "  2. Fichero kubeconfig:"
    echo "     ./scripts/configure-kubectl-hetzner.sh --kubeconfig ~/.kube/hetzner.yaml"
    echo ""
    echo "  3. hcloud CLI:"
    echo "     hcloud k8s cluster get-kubeconfig castuo-prod > ~/.kube/castuo-hetzner.yaml"
    echo "     kubectl --kubeconfig ~/.kube/castuo-hetzner.yaml get nodes"
    echo ""
    exit 1
fi

# ── Configurar KUBECONFIG ─────────────────────────────────────────────────────
export KUBECONFIG="$KUBECONFIG_FILE"

# ── Verificar conexión ────────────────────────────────────────────────────────
echo ""
echo "── Verificando conexión ────────────────────────────────"
if kubectl cluster-info --request-timeout=10s &>/dev/null; then
    ok "Conexión al cluster OK"

    echo ""
    echo "── Nodos del cluster ───────────────────────────────────"
    kubectl get nodes -o wide 2>/dev/null || warn "No se pudieron listar los nodos"

    echo ""
    echo "── Namespace castuo-system ─────────────────────────────"
    if kubectl get namespace castuo-system &>/dev/null; then
        kubectl get pods -n castuo-system 2>/dev/null || true
    else
        warn "Namespace castuo-system no existe — ejecuta: kubectl apply -f k8s/namespace.yaml"
    fi
else
    err "No se puede conectar al cluster. Verifica las credenciales."
fi

# ── Exportar para sesión actual ───────────────────────────────────────────────
echo ""
ok "Para usar en esta sesión:"
echo "  export KUBECONFIG=$KUBECONFIG_FILE"
echo ""
ok "Para usar de forma permanente (añadir a ~/.bashrc o ~/.zshrc):"
echo "  echo 'export KUBECONFIG=$KUBECONFIG_FILE' >> ~/.bashrc"
