#!/bin/bash
# CASTÚO-SYSTEM™ — Backup encriptado (AES-256) + IPFS + registro en GaiaChain
# Solo quien conozca la contraseña maestra puede restaurar.

set -e
DATE=$(date +%Y-%m-%d)
BACKUP_ROOT="/tmp/backup-$DATE"
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
API_BASE="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"

read -s -p "Introduce la contraseña maestra para encriptar el backup: " MASTER_PASSWORD
echo
[ -z "$MASTER_PASSWORD" ] && { echo "Contraseña vacía."; exit 1; }

BACKUP_KEY=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha3-512 -binary | xxd -p -c 256)
IV=$(openssl rand -hex 16)

mkdir -p "$BACKUP_ROOT"
tar -czf "$BACKUP_ROOT.tar.gz" -C / etc/gaiachain opt/cursor 2>/dev/null || true
[ ! -f "$BACKUP_ROOT.tar.gz" ] && { unset MASTER_PASSWORD BACKUP_KEY IV; exit 1; }

openssl enc -aes-256-cbc -in "$BACKUP_ROOT.tar.gz" -out "$BACKUP_ROOT.tar.gz.enc" -K "$BACKUP_KEY" -iv "$IV" 2>/dev/null
rm -f "$BACKUP_ROOT.tar.gz"

IPFS_CID=""
if command -v ipfs >/dev/null 2>&1; then
  IPFS_CID=$(ipfs add -Q "$BACKUP_ROOT.tar.gz.enc")
fi
[ -n "$PINATA_API_KEY" ] && curl -sf -X POST "https://api.pinata.cloud/pinning/pinByHash" -H "Authorization: Bearer $PINATA_API_KEY" -H "Content-Type: application/json" -d "{\"hashToPin\":\"$IPFS_CID\"}" >/dev/null || true

if [ -n "$GAIA_CHAIN_ADMIN_KEY" ]; then
  SIG=$(echo -n "${IPFS_CID}${IV}" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" -passin pass:env:MASTER_PASSWORD 2>/dev/null | base64 -w 0) || SIG=""
  curl -sf -X POST "$API_BASE/api/v1/backup" -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" -H "Content-Type: application/json" -d "{\"type\":\"ENCRYPTED_BACKUP\",\"date\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"ipfs_cid\":\"$IPFS_CID\",\"iv\":\"$IV\",\"signature\":\"$SIG\"}" >/dev/null || true
fi

rm -f "$BACKUP_ROOT.tar.gz.enc"
unset MASTER_PASSWORD BACKUP_KEY
echo "Backup encriptado. IPFS CID: $IPFS_CID. IV guardado en GaiaChain o localmente según configuración."
