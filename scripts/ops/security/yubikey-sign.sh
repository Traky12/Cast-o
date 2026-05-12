#!/bin/bash
# scripts/ops/security/yubikey-sign.sh
#
# Plantilla mejorada: firma con YubiKey + notarizacion GaiaChain (contrato minimal del repo).
#
# Uso:
#   yubikey-sign.sh <challenge> [--dry-run]

set -euo pipefail

CHALLENGE="${1:-}"
SLOT="${SLOT:-1}"
DRY_RUN=false

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-1}"
BUNKER_ID="${GAIA_BUNKER_ID:-CASTUO-01-EXTREMADURA}"

if [[ -z "$CHALLENGE" ]]; then
  echo "[ERROR] Desafio vacio. Uso: $0 <challenge> [--dry-run]" >&2
  exit 1
fi

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "[ERROR] Argumento desconocido: $1" >&2
      exit 1
      ;;
  esac
done

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd ykchalresp
require_cmd xxd
require_cmd sha256sum
require_cmd python3
require_cmd curl

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"

CHALLENGE_HEX="$(echo -n "$CHALLENGE" | xxd -p -c 200 | tr -d '\n')"
echo "[INFO] Firmando con YubiKey slot=${SLOT}..." >&2

SIGNATURE="$(ykchalresp -2 "$SLOT" "$CHALLENGE_HEX" 2>/dev/null | tr -d '\r\n' || true)"
if [[ -z "$SIGNATURE" ]]; then
  echo "[ERROR] Fallo al firmar con YubiKey (firma vacia)." >&2
  exit 1
fi

timestamp_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [[ "$DRY_RUN" == false ]] && [[ -n "$GAIA_CHAIN_API_KEY" ]]; then
  # Contrato minimal del repo: {hash, coop_id, ipfs_cid}
  # Construimos la "metadata" canonica del evento y calculamos su SHA-256 para el campo hash.
  payload="$(CHALLENGE="$CHALLENGE" SIGNATURE="$SIGNATURE" SLOT="$SLOT" TIMESTAMP="$timestamp_utc" BUNKER_ID="$BUNKER_ID" GAIA_COOP_ID="$GAIA_COOP_ID" \
python3 - <<'PY'
import json, os, hashlib

challenge = os.environ["CHALLENGE"]
signature = os.environ["SIGNATURE"]
slot = int(os.environ["SLOT"])
timestamp = os.environ["TIMESTAMP"]
bunker_id = os.environ["BUNKER_ID"]
gaia_coop_id = int(os.environ["GAIA_COOP_ID"])

metadata = {
  "event_type": "yubikey_signature",
  "challenge": challenge,
  "signature": signature,
  "yubikey_slot": slot,
  "timestamp": timestamp,
  "bunker_id": bunker_id,
}

canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8")
witness_hash = hashlib.sha256(canonical).hexdigest()

out = {"hash": witness_hash, "coop_id": gaia_coop_id, "ipfs_cid": None}
print(json.dumps(out, separators=(",", ":"), sort_keys=True))
PY
  )"

  echo "[INFO] Notarizando firma en GaiaChain..." >&2
  curl -sS -X POST "$WITNESS_URL" \
    -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" >/dev/null || true
fi

echo "$SIGNATURE"

