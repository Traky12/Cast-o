#!/usr/bin/env bash
# CASTÚO — NO rota N8N_ENCRYPTION_KEY automáticamente.
#
# Cambiar la clave de cifrado de n8n sin el procedimiento oficial deja credenciales ilegibles.
# Ver: https://docs.n8n.io/hosting/ (encryption key / backup / CLI según versión).
#
# Este script solo:
#   - genera una candidata (openssl)
#   - opcionalmente notifica al Trillizo vía trillizo_audit_notify.sh (evento "key_rotation_planned")
#
# Uso:
#   bash scripts/n8n/rotar_bunker.sh              # dry-run + aviso
#   NOTIFY=1 bash scripts/n8n/rotar_bunker.sh   # además curl al webhook si TRILLIZO_WEBHOOK_BASE está definido

set -euo pipefail

echo "================================================================"
echo "[CASTÚO] rotar_bunker.sh — rotación AUTOMÁTICA de N8N_ENCRYPTION_KEY NO soportada aquí."
echo "         Plan manual: backup del volumen .n8n, export de workflows, doc n8n, ventana de mantenimiento."
echo "================================================================"

CANDIDATE=$(openssl rand -hex 24)
echo "[INFO] Candidata (NO aplicada): N8N_ENCRYPTION_KEY=${CANDIDATE}"
echo "[INFO] Guárdala en un gestor de secretos; aplícala solo tras migración soportada por n8n."

if [[ "${NOTIFY:-0}" == "1" && -n "${TRILLIZO_WEBHOOK_BASE:-}" ]]; then
  ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
  EVENT_PAYLOAD="key_rotation_planned"
  bash "${ROOT}/scripts/n8n/trillizo_audit_notify.sh" "$EVENT_PAYLOAD" || true
fi

exit 0
