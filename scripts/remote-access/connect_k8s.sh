#!/usr/bin/env bash
# Plantilla: túnel SSH hacia la API de Kubernetes vía bastión.
# Ajustar BASTION_HOST, usuario y hostname interno del plano de control.

set -euo pipefail

USER_NAME="${1:-ctaex}"
BASTION_HOST="${BASTION_HOST:-bastion.example.local}"
BASTION_PORT="${BASTION_PORT:-2222}"
LOCAL_API_PORT="${LOCAL_API_PORT:-6443}"
# Hostname resoluble DESDE el bastión (no desde tu portátil)
K8S_INTERNAL_HOST="${K8S_INTERNAL_HOST:-kubernetes.default.svc}"

echo "Abriendo túnel: localhost:${LOCAL_API_PORT} -> ${K8S_INTERNAL_HOST}:6443 vía ${USER_NAME}@${BASTION_HOST}:${BASTION_PORT}"
echo "En otra terminal, configura kubeconfig para https://127.0.0.1:${LOCAL_API_PORT} (certificados según tu cluster)."

ssh -N -L "${LOCAL_API_PORT}:${K8S_INTERNAL_HOST}:6443" "${USER_NAME}@${BASTION_HOST}" -p "${BASTION_PORT}"
