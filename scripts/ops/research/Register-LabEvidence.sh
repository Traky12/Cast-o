#!/bin/bash
# scripts/ops/research/Register-LabEvidence.sh
#
# Notariza evidencia en GaiaChain desde:
#   - JSON por stdin, o
#   - --file informe.json (solo JSON valido), o
#   - Cualquier otro fichero existente (sobre canonico document).
#
# Uso:
#   export GAIA_CHAIN_API_KEY="..."
#   bash scripts/ops/research/Register-LabEvidence.sh informe.json
#   cat informe.json | bash scripts/ops/research/Register-LabEvidence.sh
#   bash scripts/ops/research/Register-LabEvidence.sh --file informe.json

set -euo pipefail

command -v jq >/dev/null 2>&1 || { echo "[ERROR] Falta jq." >&2; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "[ERROR] Falta curl." >&2; exit 1; }
command -v sha256sum >/dev/null 2>&1 || { echo "[ERROR] Falta sha256sum." >&2; exit 1; }

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu/api/v1/witness}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-LAB-01}"

validate_json() {
  local file="$1"
  if ! jq empty "$file" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

generate_canonical_envelope() {
  local file_path="$1"
  local resolved_path
  resolved_path="$(realpath "$file_path" 2>/dev/null)" || resolved_path="$file_path"
  local file_sha256
  file_sha256="$(sha256sum "$resolved_path" | awk '{print $1}')"
  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  jq -n \
    --arg kind "document" \
    --arg path "$resolved_path" \
    --arg sha256 "$file_sha256" \
    --arg ts "$timestamp" \
    '{
      evidence_kind: $kind,
      document_path: $path,
      document_sha256: $sha256,
      timestamp_utc: $ts
    }'
}

if [[ "$#" -eq 0 ]]; then
  if ! temp_file="$(mktemp)"; then
    echo "[ERROR] No se pudo crear archivo temporal." >&2
    exit 1
  fi
  trap 'rm -f "$temp_file"' EXIT
  cat >"$temp_file"
  if ! validate_json "$temp_file"; then
    echo "[ERROR] La entrada por stdin no es un JSON valido." >&2
    exit 1
  fi
  EVIDENCE_DATA="$(cat "$temp_file")"
elif [[ "$#" -eq 2 && "$1" == "--file" ]]; then
  if [[ ! -f "$2" ]]; then
    echo "[ERROR] Archivo no encontrado: $2" >&2
    exit 1
  fi
  if ! validate_json "$2"; then
    echo "[ERROR] El archivo '$2' no es un JSON valido. Para no-JSON: $0 \"$2\"" >&2
    exit 1
  fi
  EVIDENCE_DATA="$(cat "$2")"
elif [[ "$#" -eq 1 ]]; then
  if [[ ! -f "$1" ]]; then
    echo "[ERROR] No es un fichero: $1" >&2
    exit 1
  fi
  if validate_json "$1"; then
    EVIDENCE_DATA="$(cat "$1")"
  else
    EVIDENCE_DATA="$(generate_canonical_envelope "$1")"
  fi
else
  echo "Uso: $0 [--file <archivo.json>] o <archivo> o JSON por stdin" >&2
  exit 1
fi

EVIDENCE_HASH="$(echo "$EVIDENCE_DATA" | jq -c . | sha256sum | awk '{print $1}')"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

RESPONSE="$(
  curl -s -X POST "$GAIA_CHAIN_API_URL" \
    -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
    "hash": "'"$EVIDENCE_HASH"'",
    "coop_id": "'"$GAIA_COOP_ID"'",
    "ipfs_cid": null
  }'
)"

echo "[INFO] Evidencia notarizada en GaiaChain:"
echo "witness_payload_hash: $EVIDENCE_HASH"
echo "canonical_evidence_json: $(echo "$EVIDENCE_DATA" | jq -c .)"
echo "gaiachain_response: $RESPONSE"
