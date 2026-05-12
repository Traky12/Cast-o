#!/bin/bash
# scripts/energy_audit/Register-EnergyAudit.sh
#
# Notariza una auditoria energetica (JSON canonico) en GaiaChain (hash, coop_id, ipfs_cid).
# Uso:
#   export GAIA_CHAIN_API_KEY="..."
#   export GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-ENERGY-01}"
#   bash scripts/energy_audit/Register-EnergyAudit.sh audit_results.json

set -euo pipefail

command -v jq >/dev/null 2>&1 || { echo "[ERROR] Falta jq." >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "[ERROR] Falta curl." >&2; exit 1; }
command -v sha256sum >/dev/null 2>&1 || { echo "[ERROR] Falta sha256sum." >&2; exit 1; }

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu/api/v1/witness}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-ENERGY-01}"

if [[ -z "${1:-}" ]]; then
  echo "Uso: $0 <audit_results.json>" >&2
  exit 1
fi

AUDIT_FILE="$1"
if [[ ! -f "$AUDIT_FILE" ]]; then
  echo "[ERROR] Archivo no encontrado: $AUDIT_FILE" >&2
  exit 1
fi

if ! jq empty "$AUDIT_FILE" >/dev/null 2>&1; then
  echo "[ERROR] El archivo '$AUDIT_FILE' no es un JSON valido." >&2
  exit 1
fi

AUDIT_HASH="$(jq -c . "$AUDIT_FILE" | sha256sum | awk '{print $1}')"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

RESPONSE="$(
  curl -s -X POST "$GAIA_CHAIN_API_URL" \
    -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
    "hash": "'"$AUDIT_HASH"'",
    "coop_id": "'"$GAIA_COOP_ID"'",
    "ipfs_cid": null
  }'
)"

echo "[INFO] Auditoria energetica notarizada en GaiaChain:"
echo "witness_payload_hash: $AUDIT_HASH"
echo "gaiachain_response: $RESPONSE"
