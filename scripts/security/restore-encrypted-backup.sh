#!/bin/bash
# CASTÚO-SYSTEM™ — Restauración de backup encriptado (solo con contraseña maestra)

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
API_BASE="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"

read -s -p "Introduce la contraseña maestra para restaurar: " MASTER_PASSWORD
echo
[ -z "$MASTER_PASSWORD" ] && { echo "Contraseña vacía."; exit 1; }

BACKUP_KEY=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha3-512 -binary | xxd -p -c 256)

if [ -z "$GAIA_CHAIN_ADMIN_KEY" ]; then
  echo "Indica IPFS_CID e IV (o configura GAIA_CHAIN_ADMIN_KEY y API que devuelva backups/latest)."
  read -p "IPFS CID: " IPFS_CID
  read -p "IV (hex): " IV
else
  DATA=$(curl -sf "$API_BASE/api/v1/backups/latest" -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY")
  IPFS_CID=$(echo "$DATA" | jq -r '.ipfs_cid // empty')
  IV=$(echo "$DATA" | jq -r '.iv // empty')
fi
[ -z "$IPFS_CID" ] || [ -z "$IV" ] && { unset MASTER_PASSWORD BACKUP_KEY; exit 1; }

curl -sf "https://ipfs.io/ipfs/$IPFS_CID" -o /tmp/backup.enc
openssl enc -aes-256-cbc -d -in /tmp/backup.enc -out /tmp/backup.tar.gz -K "$BACKUP_KEY" -iv "$IV"
tar -xzf /tmp/backup.tar.gz -C /
rm -f /tmp/backup.enc /tmp/backup.tar.gz
unset MASTER_PASSWORD BACKUP_KEY
echo "Backup restaurado."
