#!/bin/bash
# scripts/ops/piloto/Register-3DModel.sh
#
# Notariza versiones de modelos 3D/4D del piloto en GaiaChain usando
# el contrato minimal del repo:
#   { "hash", "coop_id", "ipfs_cid" }
#
# - Calcula SHA-256 del archivo (si existe) y SHA-256 de metadatos canonicos.
# - Para GaiaChain se usa el hash de los metadatos canonicos (meta_hash)
#   como campo "hash" (contrato minimal).
# - Si IPFS esta disponible y se indica, puede subir el modelo y pasar ipfs_cid.
#
# Uso:
#   GAIA_CHAIN_API_KEY=... GAIA_COOP_ID=... bash Register-3DModel.sh [--file path] [--version 1.0] [--ipfs]

set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd sha256sum
require_cmd jq
require_cmd curl
require_cmd python3

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-01-EXTREMADURA}"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"
if [[ "$GAIA_CHAIN_API_URL" == *"/api/v1/witness" ]]; then
  # Permite configurar GAIA_CHAIN_API_URL ya como endpoint witness completo.
  WITNESS_URL="$GAIA_CHAIN_API_URL"
fi

MODEL_FILE=""
VERSION="1.0"
DO_IPFS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      MODEL_FILE="${2:-}"
      shift 2
      ;;
    --version)
      VERSION="${2:-}"
      shift 2
      ;;
    --ipfs)
      DO_IPFS=true
      shift 1
      ;;
    *)
      echo "[ERROR] Argumento desconocido: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$MODEL_FILE" ]]; then
  MODEL_FILE="${MODEL_FILE:-prototipo_extremadura.blend}"
fi

TS_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

MODEL_HASH=""
if [[ -f "$MODEL_FILE" ]]; then
  MODEL_HASH="$(sha256sum "$MODEL_FILE" | awk '{print $1}')"
else
  echo "[WARN] Archivo de modelo no existe: $MODEL_FILE. Usando MODEL_HASH vacio." >&2
  MODEL_HASH=""
fi

MODEL_BASENAME="$(basename "$MODEL_FILE")"

# Metadatos canonicos para fijar version del modelo
METADATA_JSON="$(jq -n \
  --arg model_type "prototype_3d" \
  --arg model_file "$MODEL_BASENAME" \
  --arg model_hash "$MODEL_HASH" \
  --arg timestamp "$TS_UTC" \
  --arg version "$VERSION" \
  '{
    model_type: $model_type,
    model_file: $model_file,
    model_hash: $model_hash,
    timestamp: $timestamp,
    version: $version,
    components: [
      {name:"terracota_modules", count:500, material:"clay"},
      {name:"pv_panels", count:10, power_w:5000},
      {name:"geotermia_pipes", length_m:200}
    ]
  }'
)"

META_HASH="$(echo "$METADATA_JSON" | jq -c . | sha256sum | awk '{print $1}')"

IPFS_CID="null"
if [[ "$DO_IPFS" == true ]]; then
  if command -v ipfs >/dev/null 2>&1; then
    if [[ -f "$MODEL_FILE" ]]; then
      CID="$(ipfs add -Q "$MODEL_FILE" || true)"
      if [[ -n "${CID:-}" ]]; then
        IPFS_CID="$CID"
      fi
    else
      echo "[WARN] No se sube a IPFS porque no existe el modelo: $MODEL_FILE" >&2
    fi
  else
    echo "[WARN] ipfs no disponible; ipfs_cid sera null" >&2
  fi
fi

export META_HASH="$META_HASH"
export IPFS_CID="$IPFS_CID"
export GAIA_COOP_ID="$GAIA_COOP_ID"

payload="$(python3 - <<'PY'
import os, json
meta_hash = os.environ["META_HASH"]
coop = os.environ["GAIA_COOP_ID"]
ipfs_cid = os.environ.get("IPFS_CID","null")
out = {"hash": meta_hash, "coop_id": coop, "ipfs_cid": (None if ipfs_cid=="null" else ipfs_cid)}
print(json.dumps(out, separators=(",",":"), sort_keys=True))
PY
)"

response="$(curl -sS -X POST "$WITNESS_URL" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$payload" || true)"

echo "[3DModel] Done."
echo " - model_file: $MODEL_BASENAME"
echo " - model_hash: $MODEL_HASH"
echo " - meta_hash: $META_HASH"
echo " - ipfs_cid: $IPFS_CID"
echo " - response: $response"

