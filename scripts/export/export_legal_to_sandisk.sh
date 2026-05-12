#!/bin/bash
# CASTÚO-SYSTEM™ — Exporta datos legales (CTAEX, compliance, auditorías) al SanDisk.
# Uso: ./scripts/export/export_legal_to_sandisk.sh

set -e
DEST="${CASTUO_SANDISK_ROOT:-/mnt/sandisk/CASTUO_SECURE}/legal"
mkdir -p "$DEST"
[ -d /opt/castuo/legal ] && cp -a /opt/castuo/legal/* "$DEST/" 2>/dev/null || true
[ -d docs/legal ] && cp -a docs/legal/* "$DEST/" 2>/dev/null || true
echo "Datos legales exportados a $DEST"
