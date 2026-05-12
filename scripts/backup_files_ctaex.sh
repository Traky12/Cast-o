#!/bin/bash
# Backup de archivos críticos CTAEX: secrets, nginx, docker config.
# Ajustar CRITICAL_DIRS según tu instalación. No incluir contraseñas en repos.
# Uso: BACKUP_DIR=/backups/files ./scripts/backup_files_ctaex.sh
# Cron: 0 4 * * * /ruta/al/repo/scripts/backup_files_ctaex.sh >> /var/log/castuo/backup_files.log 2>&1

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKUP_DIR="${BACKUPS_FILES_DIR:-/backups/files}"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Directorios a respaldar (solo los que existan)
CRITICAL_DIRS=(
  "$REPO_ROOT/docker"
  "/etc/nginx/sites-available"
  "/etc/nginx/sites-enabled"
)
# Opcional: /backups, /run/secrets (Docker) — requieren root
[ -d /backups ]    && CRITICAL_DIRS+=(/backups)
[ -d /run/secrets ] && CRITICAL_DIRS+=(/run/secrets)

for dir in "${CRITICAL_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    name=$(echo "$dir" | tr "/" "_" | sed 's/^_//')
    tar -czf "$BACKUP_DIR/files_${name}-${DATE}.tar.gz" -C "$(dirname "$dir")" "$(basename "$dir")" 2>/dev/null || true
  fi
done

find "$BACKUP_DIR" -name "files_*.tar.gz" -mtime +7 -delete 2>/dev/null || true

if [ -n "${RCLONE_REMOTE:-}" ] && command -v rclone >/dev/null 2>&1; then
  for f in "$BACKUP_DIR"/files_*-"$DATE".tar.gz; do
    [ -f "$f" ] && rclone copy "$f" "$RCLONE_REMOTE:castuo-ctaex-backups/" 2>/dev/null || true
  done
fi

echo "Backup OK: $BACKUP_DIR (files_*-$DATE.tar.gz)"
