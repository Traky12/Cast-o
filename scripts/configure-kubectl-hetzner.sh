#!/usr/bin/env bash
set -euo pipefail

MODE="auto"
SERVER_IP="89.167.5.233"
SSH_USER="root"
SSH_KEY="${HOME}/.ssh/castuo_hel1"
KUBECONFIG_PATH="${HOME}/.kube/config"

usage() {
  cat <<'EOF'
Uso: scripts/configure-kubectl-hetzner.sh [opciones]

Modos:
  --from-env-b64        Usa HETZNER_KUBECONFIG_B64 o HETZNER_KUBECONFIG
  --from-ssh            Extrae /etc/rancher/k3s/k3s.yaml por SSH
  (sin modo)            Intenta env-b64 y luego SSH

Opciones SSH:
  --server-ip <ip>      IP del nodo Hetzner (default: 89.167.5.233)
  --ssh-user <user>     Usuario SSH (default: root)
  --ssh-key <path>      Clave privada SSH (default: ~/.ssh/castuo_hel1)

EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-env-b64)
      MODE="env"
      shift
      ;;
    --from-ssh)
      MODE="ssh"
      shift
      ;;
    --server-ip)
      SERVER_IP="$2"
      shift 2
      ;;
    --ssh-user)
      SSH_USER="$2"
      shift 2
      ;;
    --ssh-key)
      SSH_KEY="$2"
      shift 2
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

mkdir -p "$(dirname "$KUBECONFIG_PATH")"

configure_from_env() {
  local b64="${HETZNER_KUBECONFIG_B64:-${HETZNER_KUBECONFIG:-}}"
  if [[ -z "$b64" ]]; then
    echo "[ERROR] HETZNER_KUBECONFIG_B64/HETZNER_KUBECONFIG no definido"
    return 1
  fi

printf '%s' "$b64" | base64 -d > "$KUBECONFIG_PATH"
chmod 600 "$KUBECONFIG_PATH"
echo "[OK] kubeconfig cargado desde variable de entorno"
}

configure_from_ssh() {
  [[ -f "$SSH_KEY" ]] || { echo "[ERROR] Clave SSH no encontrada: $SSH_KEY"; return 1; }

ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    "$SSH_USER@$SERVER_IP" "cat /etc/rancher/k3s/k3s.yaml" > "$KUBECONFIG_PATH"

sed -i "s|127.0.0.1|$SERVER_IP|g" "$KUBECONFIG_PATH"
chmod 600 "$KUBECONFIG_PATH"
echo "[OK] kubeconfig extraido por SSH desde $SERVER_IP"
}

if [[ "$MODE" == "env" ]]; then
  configure_from_env
elif [[ "$MODE" == "ssh" ]]; then
  configure_from_ssh
else
  if ! configure_from_env; then
    echo "[WARN] Fallback a metodo SSH"
    configure_from_ssh
  fi
fi

kubectl config current-context >/dev/null 2>&1 || true
kubectl get nodes
echo "[OK] kubectl conectado"
