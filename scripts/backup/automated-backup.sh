#!/bin/bash
# CASTÚO-SYSTEM™ — Backup automático diario (sincroniza con GaiaChain; encriptado).
# Ejecutar por cron: 0 3 * * * /opt/castuo/scripts/backup/automated-backup.sh
# No almacenar contraseñas; usar script encrypted-backup.sh que pide contraseña o usar clave en HSM.

set -e
CASTUO_ROOT="${CASTUO_ROOT:-/opt/castuo}"
SECURITY="$CASTUO_ROOT/scripts/security"

if [ -x "$SECURITY/encrypted-backup.sh" ]; then
  # En entorno automatizado, la contraseña debe venir de HSM o de vault (no por stdin)
  export CASTUO_BACKUP_AUTOMATED=1
  "$SECURITY/encrypted-backup.sh" 2>/dev/null || true
fi
# Sincronizar SanDisk si está montado
SANDISK="${CASTUO_SANDISK_ROOT:-/mnt/sandisk/CASTUO_SECURE}"
if [ -d "$SANDISK" ]; then
  [ -x "$CASTUO_ROOT/scripts/export/export_gaiachain_to_sandisk.sh" ] && "$CASTUO_ROOT/scripts/export/export_gaiachain_to_sandisk.sh" || true
fi
