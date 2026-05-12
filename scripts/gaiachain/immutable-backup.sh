#!/bin/bash
# CASTÚO-SYSTEM™ — Backup inmutable a IPFS + registro en GaiaChain (anti-hacking v1.0)
# Uso: PINATA_API_KEY, WEB3_STORAGE_KEY, CRUST_API_KEY, GAIA_CHAIN_API_KEY (opcionales)
# Ejemplo crontab: 0 0 * * * /opt/castuo/scripts/gaiachain/immutable-backup.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR="/tmp/gaiachain_backup_$DATE"
mkdir -p "$BACKUP_DIR"

# 1. Backup de Smart Contracts y scripts
cp -r contracts "$BACKUP_DIR/" 2>/dev/null || true
cp -r scripts/gaiachain "$BACKUP_DIR/" 2>/dev/null || true

# 2. Backup de DB (si existe pg_dump y variable DB)
if [ -n "${GAIACHAIN_DB_URL}" ] && command -v pg_dump >/dev/null 2>&1; then
  pg_dump "$GAIACHAIN_DB_URL" > "$BACKUP_DIR/gaiachain_db.sql" 2>/dev/null || true
fi

# 3. Comprimir y hash
tar -czvf "$BACKUP_DIR.tar.gz" -C /tmp "$(basename "$BACKUP_DIR")"
BACKUP_HASH=$(sha256sum "$BACKUP_DIR.tar.gz" | awk '{print $1}')

# 4. IPFS (si ipfs está instalado)
IPFS_CID=""
if command -v ipfs >/dev/null 2>&1; then
  IPFS_CID=$(ipfs add -Q "$BACKUP_DIR.tar.gz")
  echo "IPFS CID: $IPFS_CID"
fi

# 5. Pinning externo (opcional)
if [ -n "$PINATA_API_KEY" ]; then
  curl -s -X POST "https://api.pinata.cloud/pinning/pinByHash" \
    -H "Authorization: Bearer $PINATA_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"hashToPin\":\"$IPFS_CID\",\"pinataMetadata\":{\"name\":\"GaiaChain Backup $DATE\"}}" || true
fi

# 6. Registrar en GaiaChain (API interna; opcional)
if [ -n "$GAIA_CHAIN_API_KEY" ]; then
  curl -s -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/backup" \
    -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"IMMUTABLE_BACKUP\",
      \"date\": \"$DATE\",
      \"ipfs_cid\": \"$IPFS_CID\",
      \"backup_hash\": \"$BACKUP_HASH\"
    }" || true
fi

echo "Backup hash: $BACKUP_HASH"
rm -rf "$BACKUP_DIR" "$BACKUP_DIR.tar.gz"
