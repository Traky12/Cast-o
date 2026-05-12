#!/bin/bash
# scripts/ops/piloto/Register-BiopolymerTest.sh
#
# Scaffolding: Notariza resultados de validacion de polimeros metalicos biocompatibles
# en GaiaChain usando el contrato minimal del repo:
#   { "hash", "coop_id", "ipfs_cid" }
#
# Variables:
# - GAIA_CHAIN_API_URL
# - GAIA_CHAIN_API_KEY
# - GAIA_COOP_ID
#
# Uso:
#   GAIA_CHAIN_API_KEY=... bash Register-BiopolymerTest.sh --test-id TERRA-001

set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd jq
require_cmd sha256sum
require_cmd curl
require_cmd date
require_cmd python3

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-01-EXTREMADURA}"
FINCA_ID="${FINCA_ID:-CASTUO-PILOTO-EXTREMADURA-01}"

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

TEST_ID="${1:-TERRA-001}"

TS_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "[BiopolymerTest] Notarizando test (PLACEHOLDER) id=$TEST_ID"

# ==========================
# Datos (PLACEHOLDER) - adaptar a tus mediciones
# ==========================
CONDUCTIVITY_S="${CONDUCTIVITY_S:-25.0}"
BIOCOMPATIBILITY="${BIOCOMPATIBILITY:-PASS}" # PASS/FAIL (por ejemplo de ISO 10993-5)
DURABILITY_PASS="${DURABILITY_PASS:-PASS}"

TEST_DATA="$(jq -n \
  --arg finca_id "$FINCA_ID" \
  --arg test_id "$TEST_ID" \
  --arg test_type "biopolymer_validation" \
  --arg conductivity_s "$CONDUCTIVITY_S" \
  --arg biocompatibility "$BIOCOMPATIBILITY" \
  --arg durability_pass "$DURABILITY_PASS" \
  --arg timestamp "$TS_UTC" \
  '{
    finca_id: $finca_id,
    test_id: $test_id,
    test_type: $test_type,
    conductivity_s: ($conductivity_s|tonumber),
    biocompatibility: $biocompatibility,
    durability_pass: $durability_pass,
    timestamp: $timestamp
  }')"

HASH="$(echo "$TEST_DATA" | jq -c . | sha256sum | awk '{print $1}')"

payload="$(python3 - <<'PY'
import json, os
hashv = os.environ["HASH"]
coop = os.environ["GAIA_COOP_ID"]
out = {"hash": hashv, "coop_id": coop, "ipfs_cid": None}
print(json.dumps(out, separators=(",", ":"), sort_keys=True))
PY
)"

echo "[BiopolymerTest] witness payload hash=$HASH"

response="$(curl -sS -X POST "$WITNESS_URL" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$payload" || true)"

echo "[BiopolymerTest] Done response=$response"

