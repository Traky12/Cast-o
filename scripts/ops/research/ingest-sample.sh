#!/bin/bash
# scripts/ops/research/ingest-sample.sh
#
# Registra ingesta de muestra con cadena de custodia: hash SHA-256 del fichero +
# metadatos en JSON canonico; witness GaiaChain minimal { hash, coop_id, ipfs_cid }.
#
# Uso:
#   GAIA_CHAIN_API_KEY=... GAIA_COOP_ID=CASTUO-LAB-01 \
#     bash ingest-sample.sh /ruta/muestra.bin /ruta/metadata.json
#
# Opcional:
#   RUN_CLAMAV=1           -> ejecuta clamscan; si detecta y ALLOW_INFECTED_SAMPLE no es 1, falla.
#   ALLOW_INFECTED_SAMPLE=1 -> permite muestra con deteccion ClamAV (laboratorio de malware).
#   UPLOAD_IPFS=1          -> ipfs add y segundo POST con mismo hash (si vuestro witness lo permite).
#
# ClamAV en laboratorio de malware: normalmente NO usar RUN_CLAMAV=1 en ingesta, o usar ALLOW_INFECTED_SAMPLE=1.

set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd jq
require_cmd sha256sum
require_cmd curl
require_cmd python3

SAMPLE_PATH="${1:-}"
METADATA_FILE="${2:-}"

if [[ -z "$SAMPLE_PATH" || -z "$METADATA_FILE" ]]; then
  echo "Uso: $0 <muestra> <metadata.json>" >&2
  exit 1
fi

if [[ ! -f "$SAMPLE_PATH" ]]; then
  echo "[ERROR] Muestra no encontrada: $SAMPLE_PATH" >&2
  exit 1
fi

if [[ ! -f "$METADATA_FILE" ]]; then
  echo "[ERROR] Metadata no encontrada: $METADATA_FILE" >&2
  exit 1
fi

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}"
GAIA_COOP_ID="${GAIA_COOP_ID:-CASTUO-LAB-01}"

if [[ -z "$GAIA_CHAIN_API_KEY" ]]; then
  echo "[ERROR] GAIA_CHAIN_API_KEY no configurada." >&2
  exit 1
fi

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"
if [[ "$GAIA_CHAIN_API_URL" == *"/api/v1/witness" ]]; then
  WITNESS_URL="$GAIA_CHAIN_API_URL"
fi

if [[ "${RUN_CLAMAV:-0}" == "1" ]]; then
  if command -v clamscan >/dev/null 2>&1; then
    if ! clamscan --quiet "$SAMPLE_PATH"; then
      if [[ "${ALLOW_INFECTED_SAMPLE:-0}" != "1" ]]; then
        echo "[ERROR] ClamAV detecto firma. Para laboratorio de malware use ALLOW_INFECTED_SAMPLE=1 o desactive RUN_CLAMAV." >&2
        exit 1
      fi
      echo "[WARN] ClamAV: deteccion esperada en laboratorio; continua por ALLOW_INFECTED_SAMPLE=1."
    fi
  else
    echo "[WARN] clamscan no disponible; se omite escaneo."
  fi
fi

SAMPLE_HASH="$(sha256sum "$SAMPLE_PATH" | awk '{print $1}')"
METADATA_JSON="$(jq -c . "$METADATA_FILE")"
TS_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

export SAMPLE_HASH METADATA_JSON TS_UTC

PAYLOAD_HASH="$(python3 - <<'PY'
import hashlib, json, os
meta = json.loads(os.environ["METADATA_JSON"])
rec = {
    "action": "ingest",
    "sample_sha256": os.environ["SAMPLE_HASH"],
    "metadata": meta,
    "timestamp_utc": os.environ["TS_UTC"],
}
canon = json.dumps(rec, sort_keys=True, separators=(",", ":"))
print(hashlib.sha256(canon.encode("utf-8")).hexdigest())
PY
)"

export PAYLOAD_HASH GAIA_COOP_ID

witness_body="$(python3 - <<'PY'
import json, os
h = os.environ["PAYLOAD_HASH"]
coop = os.environ["GAIA_COOP_ID"]
print(json.dumps({"hash": h, "coop_id": coop, "ipfs_cid": None}, separators=(",", ":"), sort_keys=True))
PY
)"

echo "[ingest-sample] witness hash=$PAYLOAD_HASH (sample_sha256=$SAMPLE_HASH)"
response="$(curl -sS -X POST "$WITNESS_URL" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$witness_body" || true)"

echo "[ingest-sample] response=$response"

IPFS_CID="null"
if [[ "${UPLOAD_IPFS:-0}" == "1" ]] && command -v ipfs >/dev/null 2>&1; then
  IPFS_CID="$(ipfs add -Q "$SAMPLE_PATH" || true)"
  if [[ -n "$IPFS_CID" && "$IPFS_CID" != "null" ]]; then
    export IPFS_CID
    witness_ipfs="$(python3 - <<'PY'
import json, os
h = os.environ["PAYLOAD_HASH"]
coop = os.environ["GAIA_COOP_ID"]
cid = os.environ["IPFS_CID"]
print(json.dumps({"hash": h, "coop_id": coop, "ipfs_cid": cid}, separators=(",", ":"), sort_keys=True))
PY
)"
    echo "[ingest-sample] actualizando witness con ipfs_cid=$IPFS_CID"
    curl -sS -X POST "$WITNESS_URL" \
      -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
      -H "Content-Type: application/json" \
      -d "$witness_ipfs" || true
  fi
fi
