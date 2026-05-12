#!/bin/bash
# CASTÚO-SYSTEM™ — Exporta firmware IoT y certificados TPM al SanDisk.
# Uso: ./scripts/export/export_iot_to_sandisk.sh

set -e
DEST="${CASTUO_SANDISK_ROOT:-/mnt/sandisk/CASTUO_SECURE}/iot"
mkdir -p "$DEST"/{firmware,certs}
[ -d /opt/castuo/iot/firmware ] && cp -a /opt/castuo/iot/firmware/* "$DEST/firmware/" 2>/dev/null || true
[ -d /opt/castuo/iot/certs ] && cp -a /opt/castuo/iot/certs/* "$DEST/certs/" 2>/dev/null || true
echo "IoT exportado a $DEST"
