#!/usr/bin/env bash
set -euo pipefail

# Backup soberano UE: evidencia crítica de trazabilidad THC + modelos.
BACKUP_ROOT="${BACKUP_ROOT:-/backups/castuo}"
DATE_TAG="$(date +%Y%m%d_%H%M%S)"
POSTGRES_DIR="${BACKUP_ROOT}/postgres/${DATE_TAG}"
MODELS_DIR="${BACKUP_ROOT}/models/${DATE_TAG}"

mkdir -p "${POSTGRES_DIR}" "${MODELS_DIR}"

DB_NAME="${DB_NAME:-castuo_ctaex}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  --table=public.spectra_estimations \
  > "${POSTGRES_DIR}/spectra_estimations.sql"

cp -r backend/models/* "${MODELS_DIR}/"

sha256sum "${POSTGRES_DIR}/spectra_estimations.sql" > "${POSTGRES_DIR}/SHA256SUMS.txt"

# Requiere remote "scaleway" configurado en rclone.
rclone copy "${POSTGRES_DIR}" "scaleway:castuo-backups/postgres/${DATE_TAG}" --s3-acl=private
rclone copy "${MODELS_DIR}" "scaleway:castuo-backups/models/${DATE_TAG}" --s3-acl=private

echo "Backup completado: ${DATE_TAG}"
