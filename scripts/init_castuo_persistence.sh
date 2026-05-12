#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_FILE="$ROOT_DIR/scripts/db/init_castuo_system_schema.sql"
DB_CONTAINER="${DB_CONTAINER:-castuo-mariadb}"
DB_ROOT_PASSWORD="${WP_DB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-}}"

if [[ ! -f "$SQL_FILE" ]]; then
  echo "[ERROR] SQL no encontrado: $SQL_FILE" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker no disponible en PATH" >&2
  exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -qx "$DB_CONTAINER"; then
  echo "[ERROR] El contenedor $DB_CONTAINER no está corriendo" >&2
  exit 1
fi

if [[ -z "$DB_ROOT_PASSWORD" ]]; then
  echo "[ERROR] Define WP_DB_ROOT_PASSWORD o MYSQL_ROOT_PASSWORD para inicializar la persistencia" >&2
  exit 1
fi

echo "[INFO] Inicializando persistencia en MariaDB ($DB_CONTAINER)..."
docker exec -i "$DB_CONTAINER" mariadb -uroot -p"$DB_ROOT_PASSWORD" < "$SQL_FILE"

echo "[INFO] Verificando bases de datos..."
docker exec -i "$DB_CONTAINER" mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "SHOW DATABASES;"

echo "[INFO] Verificando tablas críticas..."
docker exec -i "$DB_CONTAINER" mariadb -uroot -p"$DB_ROOT_PASSWORD" -e "USE castuo_system; SHOW TABLES;"

echo "[OK] Persistencia inicializada: users, farms, transactions, logs"
