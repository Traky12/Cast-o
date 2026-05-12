#!/bin/bash
# Backup PostgreSQL CTAEX (castuo_ctaex). Ejecutar desde la raíz del repo.
# Uso: BACKUP_DIR=/backups/postgres ./scripts/backup_postgres_ctaex.sh
# Cron: 0 2 * * * /ruta/al/repo/scripts/backup_postgres_ctaex.sh >> /var/log/castuo/backup_postgres.log 2>&1

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-$REPO_ROOT/docker/docker-compose.ctaex.yml}"
BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-castuo_ctaex}"
DB_USER="${DB_USER:-castuo_admin}"

mkdir -p "$BACKUP_DIR"

# pg_dump desde contenedor postgres
if [ -f "$COMPOSE_FILE" ]; then
  docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$DB_NAME-$DATE.sql.gz"
else
  echo "No encontrado: $COMPOSE_FILE. Definir COMPOSE_FILE o ejecutar desde repo."
  exit 1
fi

# Eliminar backups antiguos (+30 días)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete 2>/dev/null || true

# Opcional: subir a Backblaze B2 (requiere rclone configurado)
if [ -n "${RCLONE_REMOTE:-}" ] && command -v rclone >/dev/null 2>&1; then
  rclone copy "$BACKUP_DIR/$DB_NAME-$DATE.sql.gz" "$RCLONE_REMOTE:castuo-ctaex-backups/" 2>/dev/null || true
fi

echo "Backup OK: $BACKUP_DIR/$DB_NAME-$DATE.sql.gz"
