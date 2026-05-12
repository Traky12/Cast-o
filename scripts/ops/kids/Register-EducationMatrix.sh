#!/bin/bash
# scripts/ops/kids/Register-EducationMatrix.sh
#
# Notariza en GaiaChain el hash SHA-256 del documento canonico de validacion
# educativa (contrato minimal del repo: hash, coop_id, ipfs_cid).
#
# Uso:
#   GAIA_CHAIN_API_KEY=... GAIA_COOP_ID=CASTUO-EDU-01 bash Register-EducationMatrix.sh [ruta_al_md]

set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd sha256sum
require_cmd curl
require_cmd python3

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DOC="${1:-$ROOT_DIR/docs/ops/kids/validacion-por-edad-y-nivel-educativo-2026.md}"

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-EDU-01}"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

if [[ ! -f "$DOC" ]]; then
  echo "[ERROR] Documento no encontrado: $DOC" >&2
  exit 1
fi

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"
if [[ "$GAIA_CHAIN_API_URL" == *"/api/v1/witness" ]]; then
  WITNESS_URL="$GAIA_CHAIN_API_URL"
fi

HASH="$(sha256sum "$DOC" | awk '{print $1}')"
export HASH GAIA_COOP_ID

payload="$(python3 - <<'PY'
import json, os
h = os.environ["HASH"]
coop = os.environ["GAIA_COOP_ID"]
print(json.dumps({"hash": h, "coop_id": coop, "ipfs_cid": None}, separators=(",", ":"), sort_keys=True))
PY
)"

echo "[EducationMatrix] Notarizando witness..."
response="$(curl -sS -X POST "$WITNESS_URL" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$payload" || true)"

echo "[EducationMatrix] file=$DOC hash=$HASH response=$response"
