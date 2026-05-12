#!/bin/bash
# docs/ops/gitlab-selfhosted/backup_to_ipfs.sh
#
# Script de backup de GitLab a IPFS con notarizacion opcional en GaiaChain.
#
# Importante (soberania y no dependencia externa):
# - Mantiene llaves fuera del repo: GAIA_CHAIN_API_KEY y posibles tokens deben venir de entorno.
# - Witness usa contrato minimal del repo: {"hash","coop_id","ipfs_cid"}.
#
# Requisitos:
# - Comando `gitlab-backup` disponible.
# - CLI `ipfs` disponible.
# - `curl` disponible.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/opt/gitlab/backups}"
IPFS_API_ADDR="${IPFS_API_ADDR:-127.0.0.1:5001}"

GAIA_CHAIN_API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.eu}"
GAIA_CHAIN_API_KEY="${GAIA_CHAIN_API_KEY:-}" # requerido si quieres notarizar
GAIA_COOP_ID="${GAIA_COOP_ID:-1}"

IPFS_GATEWAY_MODE="${IPFS_GATEWAY_MODE:-cli}" # placeholder; script usa CLI ipfs add

WITNESS_URL="${GAIA_CHAIN_API_URL%/}/api/v1/witness"

log() {
  echo "[gitlab-backup-ipfs] $*"
}

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Falta comando requerido: $1"
}

require_cmd gitlab-backup
require_cmd ipfs
require_cmd curl
require_cmd sha256sum
require_cmd python3

log "Iniciando backup de GitLab..."
gitlab-backup create

log "Buscando backup mas reciente en: $BACKUP_DIR"
LATEST_BACKUP="$(ls -t "$BACKUP_DIR"/*_gitlab_backup.tar 2>/dev/null | head -n 1 || true)"
[[ -n "${LATEST_BACKUP:-}" ]] || fail "No se encontro backup *_gitlab_backup.tar en $BACKUP_DIR"

log "Backup encontrado: $LATEST_BACKUP"

log "Subiendo backup a IPFS..."
# ipfs add retorna varias lineas; -Q reduce a solo CID
CID="$(ipfs add -Q "$LATEST_BACKUP")"
[[ -n "${CID:-}" ]] || fail "ipfs add no devolvio CID"
log "CID IPFS: $CID"

backup_sha256="$(sha256sum "$LATEST_BACKUP" | awk '{print $1}')"
log "SHA256 backup: $backup_sha256"

if [[ -n "$GAIA_CHAIN_API_KEY" ]]; then
  log "Notarizando en GaiaChain (endpoint witness)..."

  # 1b) Verificar integridad del CID antes de notarizar:
  # - Tomamos el contenido desde IPFS (cat) y recalculamos SHA-256.
  VERIFIED_TMP="/tmp/verified_backup.tar"
  rm -f "$VERIFIED_TMP" || true
  ipfs cat "$CID" > "$VERIFIED_TMP"
  verified_sha256="$(sha256sum "$VERIFIED_TMP" | awk '{print $1}')"
  rm -f "$VERIFIED_TMP" || true

  if [[ "$backup_sha256" != "$verified_sha256" ]]; then
    fail "Checksum mismatch. local=$backup_sha256 ipfs=$verified_sha256"
  fi
  log "Integridad verificada: checksum coincide ($verified_sha256)"

  export backup_sha256
  export cid="$CID"
  export gaia_coop_id="$GAIA_COOP_ID"
  export bunker_id="${GAIA_BUNKER_ID:-CASTUO-01-EXTREMADURA}"
  export backup_file="$(basename "$LATEST_BACKUP")"
  export timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  # 2) Construir hash witness incorporando checksum (y la metadata del backup).
  # Contrato minimal del repo para /api/v1/witness:
  #   { "hash": <SHA256(canonical_json_of_metadata)>, "coop_id": <int>, "ipfs_cid": <cid> }
  payload="$(python3 - <<'PY'
import json, os, hashlib

backup_sha256 = os.environ["backup_sha256"]
cid = os.environ["cid"]
gaia_coop_id = int(os.environ.get("gaia_coop_id","1"))
bunker_id = os.environ.get("bunker_id","CASTUO-01-EXTREMADURA")

timestamp = os.environ.get("timestamp","")
obj = {
  "data_type": "gitlab_backup",
  "data_hash": cid,
  "metadata": {
    "backup_file": os.environ.get("backup_file",""),
    "checksum_sha256": backup_sha256,
    "timestamp": timestamp,
    "bunker_id": bunker_id,
    "status": "verified"
  }
}

canonical = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
witness_hash = hashlib.sha256(canonical).hexdigest()

out = {"hash": witness_hash, "coop_id": gaia_coop_id, "ipfs_cid": cid}
print(json.dumps(out, separators=(",",":"), sort_keys=True))
PY
  )"

  response="$(curl -sS -X POST "$WITNESS_URL" \
    -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" || true)"

  log "Respuesta witness (raw): $response"
else
  log "GAIA_CHAIN_API_KEY no configurada; omitiendo notarizacion en GaiaChain."
fi

log "Proceso finalizado. CID=$CID"

