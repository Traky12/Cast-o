#!/bin/bash
# Backup datos GaiaChain / nodo blockchain CTAEX.
# Si usas un contenedor con volumen de datos (ej. ganache), ajusta CONTAINER_GAIA y VOLUME_PATH.
# Uso: BACKUP_DIR=/backups/gaiachain ./scripts/backup_gaiachain_ctaex.sh
# Cron: 0 3 * * * /ruta/al/repo/scripts/backup_gaiachain_ctaex.sh >> /var/log/castuo/backup_gaiachain.log 2>&1

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/gaiachain}"
DATE=$(date +%Y%m%d_%H%M%S)
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

mkdir -p "$BACKUP_DIR"

# Opción 1: volumen Docker con nombre conocido (descomentar y ajustar si tienes nodo GaiaChain)
# CONTAINER_GAIA="${CONTAINER_GAIA:-castuo-ctaex_gaia-chain_1}"
# docker exec "$CONTAINER_GAIA" sh -c "tar -czf - -C /root ." > "$BACKUP_DIR/gaiachain-$DATE.tar.gz" 2>/dev/null || true

# Opción 2: directorio local con estado/chain (ej. después de exportar desde backend)
DATA_DIR="${GAIA_CHAIN_DATA:-$REPO_ROOT/data/gaiachain}"
if [ -d "$DATA_DIR" ]; then
  tar -czf "$BACKUP_DIR/gaiachain-$DATE.tar.gz" -C "$(dirname "$DATA_DIR")" "$(basename "$DATA_DIR")"
else
  echo "No existe GAIA_CHAIN_DATA ($DATA_DIR). Creando archivo placeholder para retención."
  touch "$BACKUP_DIR/gaiachain-$DATE.placeholder"
fi

find "$BACKUP_DIR" -name "gaiachain-*.tar.gz" -mtime +30 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.placeholder" -mtime +30 -delete 2>/dev/null || true

if [ -n "${RCLONE_REMOTE:-}" ] && command -v rclone >/dev/null 2>&1; then
  [ -f "$BACKUP_DIR/gaiachain-$DATE.tar.gz" ] && rclone copy "$BACKUP_DIR/gaiachain-$DATE.tar.gz" "$RCLONE_REMOTE:castuo-ctaex-backups/" 2>/dev/null || true
fi

echo "Backup OK: $BACKUP_DIR (gaiachain-$DATE.*)"
