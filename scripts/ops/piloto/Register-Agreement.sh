#!/bin/bash
# scripts/ops/piloto/Register-Agreement.sh
#
# Notariza un acuerdo de colaboracion (documento) en GaiaChain.
# Contrato minimal del repo:
#   { "hash", "coop_id", "ipfs_cid" }
#
# Uso:
#   GAIA_CHAIN_API_KEY=... GAIA_COOP_ID=... bash Register-Agreement.sh \
#     --file docs/ops/pilotos/ctaex-acuerdo-prototipo-agrovoltaica-terracota.md

set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd sha256sum
require_cmd jq
require_cmd curl
require_cmd date
require_cmd python3

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-01-EXTREMADURA}"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"

FILE_PATH=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      FILE_PATH="${2:-}"
      shift 2
      ;;
    *)
      echo "[ERROR] Argumento desconocido: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$FILE_PATH" ]]; then
  echo "[ERROR] Falta --file <ruta>." >&2
  exit 1
fi

if [[ ! -f "$FILE_PATH" ]]; then
  echo "[ERROR] No existe el archivo: $FILE_PATH" >&2
  exit 1
fi

TS_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
hashv="$(sha256sum "$FILE_PATH" | awk '{print $1}')"

payload="$(python3 - <<'PY'
import json, os
hashv = os.environ["HASH"]
coop = os.environ["GAIA_COOP_ID"]
out = {"hash": hashv, "coop_id": coop, "ipfs_cid": None}
print(json.dumps(out, separators=(",", ":"), sort_keys=True))
PY
)"

response="$(curl -sS -X POST "$WITNESS_URL" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$payload" || true)"

echo "[Agreement] witness hash=$hashv response=$response file=$FILE_PATH timestamp=$TS_UTC"

