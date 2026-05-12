#!/bin/bash
# CASTÚO-SYSTEM™ — Exporta backups y datos GaiaChain al SanDisk.
# Uso: ./scripts/export/export_gaiachain_to_sandisk.sh

set -e
DEST="${CASTUO_SANDISK_ROOT:-/mnt/sandisk/CASTUO_SECURE}/gaiachain"
mkdir -p "$DEST"
[ -d /opt/gaiachain/backups ] && cp -a /opt/gaiachain/backups/* "$DEST/" 2>/dev/null || true
[ -d /var/lib/gaiachain ] && tar -czf "$DEST/snapshot_$(date +%Y%m%d).tar.gz" -C /var/lib/gaiachain . 2>/dev/null || true
echo "GaiaChain exportado a $DEST"
