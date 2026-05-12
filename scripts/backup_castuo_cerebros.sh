#!/usr/bin/env bash
# Backup diario: Postgres (docker-compose.cerebros.yml) + carpetas Markdown cerebros/.
# Requisitos: docker, tar; ejecutar desde la raíz del repo Castuo-System.
# Opcional: .env.cerebros con CEREBROS_POSTGRES_* y PGPASSWORD para pg_dump no interactivo.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env.cerebros ]]; then
  set -a
  # shellcheck source=/dev/null
  source .env.cerebros
  set +a
fi

FECHA="$(date -u +%Y-%m-%dT%H-%MZ)"
DEST_ROOT="${CASTUO_BACKUP_ROOT:-$ROOT/backups/castuo-cerebros}"
DEST="$DEST_ROOT/$FECHA"
mkdir -p "$DEST/postgres" "$DEST/tar"

COMPOSE=(docker compose -f docker-compose.cerebros.yml)
[[ -f .env.cerebros ]] && COMPOSE+=(--env-file .env.cerebros)

echo "=== CASTÚO backup cerebros [$FECHA] → $DEST ==="

if "${COMPOSE[@]}" ps --status running --quiet postgres-cerebros 2>/dev/null | grep -q .; then
  echo "[1/2] pg_dump (servicio postgres-cerebros)…"
  export PGPASSWORD="${CEREBROS_POSTGRES_PASSWORD:-}"
  "${COMPOSE[@]}" exec -T -e PGPASSWORD postgres-cerebros \
    pg_dump -U "${CEREBROS_POSTGRES_USER:-agri_brain}" -d "${CEREBROS_POSTGRES_DB:-agri_brain}" -Fc \
    >"$DEST/postgres/agri_brain_${FECHA}.dump"
  echo "     → $DEST/postgres/agri_brain_${FECHA}.dump"
else
  echo "[1/2] Omitido: postgres-cerebros no está en ejecución."
fi

echo "[2/2] Tarball auditoría + soberano…"
tar -czf "$DEST/tar/cerebros_${FECHA}.tar.gz" cerebros/auditoria cerebros/soberano 2>/dev/null || {
  echo "     Aviso: alguna ruta no existe; revisa cerebros/"
  tar -czf "$DEST/tar/cerebros_${FECHA}.tar.gz" cerebros/auditoria || true
}
echo "     → $DEST/tar/cerebros_${FECHA}.tar.gz"

if [[ "${CASTUO_BACKUP_PRUNE_DAYS:-0}" =~ ^[0-9]+$ ]] && [[ "${CASTUO_BACKUP_PRUNE_DAYS}" -gt 0 ]]; then
  echo "Rotación: borrando backups en $DEST_ROOT más antiguos que ${CASTUO_BACKUP_PRUNE_DAYS} días…"
  find "$DEST_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime "+${CASTUO_BACKUP_PRUNE_DAYS}" -exec rm -rf {} \; 2>/dev/null || true
fi

echo "=== Fin ==="
