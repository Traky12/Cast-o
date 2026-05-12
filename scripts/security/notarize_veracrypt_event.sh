#!/bin/bash
# scripts/security/notarize_veracrypt_event.sh
#
# Registra un witness de VeraCrypt en GaiaChain (POST /api/v1/witness) usando el contrato minimo del repo:
#   { "hash": <sha256(data)>, "coop_id": <int>, "ipfs_cid": null }
#
set -euo pipefail

ACTION="${1:-}"
CONTAINER_PATH="${2:-}"
STATUS="${3:-success}"
TIMESTAMP="${4:-$(date -u +"%Y-%m-%dT%H:%M:%SZ")}"

if [[ -z "$ACTION" || -z "$CONTAINER_PATH" ]]; then
  echo "Usage: $0 <action> <container_path> [status] [timestamp]" >&2
  exit 1
fi

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://api.gaiachain.castuo-system.com}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
COOP_ID="${COOP_ID:-1}"

DATA_JSON="$(python - <<PY
import json
print(json.dumps({
  "event_type":"veracrypt_activity",
  "timestamp": "$TIMESTAMP",
  "data":{
    "action":"$ACTION",
    "container":"$CONTAINER_PATH",
    "status":"$STATUS",
    "bunker_id":"CASTUO-01-EXTREMADURA"
  }
}, sort_keys=True))
PY
)"

DATA_HASH="$(python - <<PY
import hashlib,sys
data = sys.stdin.read()
print(hashlib.sha256(data.encode("utf-8")).hexdigest())
PY
<<< "$DATA_JSON")"

PAYLOAD="$(python - <<PY
import json
print(json.dumps({"hash":"$DATA_HASH","coop_id": $COOP_ID, "ipfs_cid": None}))
PY
)"

curl_args=(-sS -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$GAIA_CHAIN_API_URL/api/v1/witness")
if [[ -n "$GAIA_CHAIN_API_KEY" ]]; then
  curl_args=(-sS -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" -d "$PAYLOAD" "$GAIA_CHAIN_API_URL/api/v1/witness")
fi

echo "Notarizando witness en GaiaChain ..."
set +e
resp="$(curl "${curl_args[@]}")"
code=$?
set -e

if [[ $code -ne 0 ]]; then
  echo "Witness request failed." >&2
  exit $code
fi

echo "$resp"

