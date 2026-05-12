#!/bin/bash
# Backup PostgreSQL CASTÚO JEREMIE — local y opcional OVH S3
set -euo pipefail

DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"
LOG_FILE="${BACKUP_DIR}/backup_${DATE}.log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "Iniciando backup a las $(date)"

# 1. Backup PostgreSQL (desde host: requiere pg_dump accesible)
if [ -n "${POSTGRES_PASSWORD:-}" ] && [ -n "${POSTGRES_DB:-}" ]; then
  export PGPASSWORD="${POSTGRES_PASSWORD}"
  DUMP_FILE="${BACKUP_DIR}/castuo_${DATE}.dump"
  pg_dump -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-castuo_user}" -d "${POSTGRES_DB}" -Fc > "$DUMP_FILE" || true
  unset PGPASSWORD
  if [ -f "$DUMP_FILE" ]; then
    sha256sum "$DUMP_FILE" > "${DUMP_FILE}.sha256"
    echo "Backup creado: $DUMP_FILE"
  fi
else
  echo "Variables POSTGRES_* no configuradas. Ejecutar desde contenedor postgres o definir env."
fi

# 2. Limpiar backups antiguos (>7 días)
find "${BACKUP_DIR}" -name "castuo_*.dump" -mtime +7 -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "castuo_*.sha256" -mtime +7 -delete 2>/dev/null || true
find "${BACKUP_DIR}" -name "backup_*.log" -mtime +30 -delete 2>/dev/null || true

echo "Backup finalizado: $LOG_FILE"
