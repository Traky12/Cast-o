#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME_DIR="$ROOT_DIR/wp-content/themes/castuo-agritech"
FRONTEND_PORT="${FRONTEND_PORT:-5432}"
CHECK_ONLY="false"
INIT_CONTENT="false"
OPEN_BROWSER="false"

WP_DB_NAME="${WP_DB_NAME:-wordpress}"
WP_DB_USER="${WP_DB_USER:-wordpress}"
WP_DB_PASSWORD="${WP_DB_PASSWORD:-wordpress}"
WP_DB_ROOT_PASSWORD="${WP_DB_ROOT_PASSWORD:-castuo_root}"

WP_SITE_TITLE="${WP_SITE_TITLE:-CASTUO Frontend}"
WP_ADMIN_USER="${WP_ADMIN_USER:-castuo_admin}"
WP_ADMIN_PASSWORD="${WP_ADMIN_PASSWORD:-CastuoAdmin!2026}"
WP_ADMIN_EMAIL="${WP_ADMIN_EMAIL:-admin@castuo.local}"

for arg in "$@"; do
  case "$arg" in
    --check)
      CHECK_ONLY="true"
      ;;
    --init-content)
      INIT_CONTENT="true"
      ;;
    --open)
      OPEN_BROWSER="true"
      ;;
    *)
      echo "Uso: $0 [--check] [--init-content] [--open]" >&2
      exit 2
      ;;
  esac
done

if [[ "$CHECK_ONLY" == "true" ]]; then
  if docker ps --format '{{.Names}}' | grep -qx 'castuo-wordpress' && curl -s -o /dev/null -I --max-time 5 "http://localhost:${FRONTEND_PORT}"; then
    echo "CHECK_OK frontend activo en http://localhost:${FRONTEND_PORT}"
    exit 0
  fi
  echo "CHECK_FAIL frontend no disponible en http://localhost:${FRONTEND_PORT}" >&2
  exit 1
fi

if [[ ! -d "$THEME_DIR" ]]; then
  echo "Tema no encontrado: $THEME_DIR" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker no disponible en PATH" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl no disponible en PATH" >&2
  exit 1
fi

docker network inspect castuo-wp-net >/dev/null 2>&1 || docker network create castuo-wp-net
docker volume inspect castuo_mariadb_data >/dev/null 2>&1 || docker volume create castuo_mariadb_data >/dev/null

docker rm -f castuo-wordpress >/dev/null 2>&1 || true

if ! docker ps -a --format '{{.Names}}' | grep -qx 'castuo-mariadb'; then
  docker run -d --name castuo-mariadb --network castuo-wp-net \
    --restart unless-stopped \
    --memory 512m \
    --cpus 1 \
    -e MYSQL_ROOT_PASSWORD="${WP_DB_ROOT_PASSWORD}" \
    -e MYSQL_DATABASE="${WP_DB_NAME}" \
    -e MYSQL_USER="${WP_DB_USER}" \
    -e MYSQL_PASSWORD="${WP_DB_PASSWORD}" \
    --health-cmd "mysqladmin ping -h 127.0.0.1 -u root --password='${WP_DB_ROOT_PASSWORD}'" \
    --health-interval 10s \
    --health-timeout 5s \
    --health-retries 3 \
    --health-start-period 30s \
    -v castuo_mariadb_data:/var/lib/mysql \
    mariadb:11.2 >/dev/null
elif ! docker ps --format '{{.Names}}' | grep -qx 'castuo-mariadb'; then
  docker start castuo-mariadb >/dev/null
fi

docker run -d --name castuo-wordpress --network castuo-wp-net \
  --restart unless-stopped \
  --memory 1g \
  --cpus 2 \
  -p "127.0.0.1:${FRONTEND_PORT}:80" \
  -e WORDPRESS_DB_HOST=castuo-mariadb:3306 \
  -e WORDPRESS_DB_USER="${WP_DB_USER}" \
  -e WORDPRESS_DB_PASSWORD="${WP_DB_PASSWORD}" \
  -e WORDPRESS_DB_NAME="${WP_DB_NAME}" \
  --health-cmd "curl -f http://127.0.0.1/wp-login.php || exit 1" \
  --health-interval 30s \
  --health-timeout 5s \
  --health-retries 3 \
  --health-start-period 45s \
  -v "$THEME_DIR":/var/www/html/wp-content/themes/castuo-agritech \
  wordpress:6.6-php8.2-apache >/dev/null

for _ in $(seq 1 30); do
  if curl -s -o /dev/null -I --max-time 3 "http://localhost:${FRONTEND_PORT}"; then
    break
  fi
  sleep 1
done

if [[ "$INIT_CONTENT" == "true" ]]; then
  curl -s -L "http://localhost:${FRONTEND_PORT}/wp-admin/install.php?step=2" \
    --data-urlencode "weblog_title=${WP_SITE_TITLE}" \
    --data-urlencode "user_name=${WP_ADMIN_USER}" \
    --data-urlencode "admin_password=${WP_ADMIN_PASSWORD}" \
    --data-urlencode "admin_password2=${WP_ADMIN_PASSWORD}" \
    --data-urlencode "admin_email=${WP_ADMIN_EMAIL}" \
    --data-urlencode "blog_public=0" \
    --data-urlencode "Submit=Install WordPress" >/dev/null || true

  PREFIX="$(docker exec castuo-mariadb mariadb -N -u"${WP_DB_USER}" -p"${WP_DB_PASSWORD}" "${WP_DB_NAME}" -e "SHOW TABLES LIKE '%_options';" | head -n 1 | sed 's/options$//')"
  if [[ -n "$PREFIX" ]]; then
    docker exec castuo-mariadb mariadb -u"${WP_DB_USER}" -p"${WP_DB_PASSWORD}" "${WP_DB_NAME}" -e "
      UPDATE ${PREFIX}options SET option_value='http://localhost:${FRONTEND_PORT}' WHERE option_name IN ('siteurl','home');
      UPDATE ${PREFIX}options SET option_value='castuo-agritech' WHERE option_name IN ('template','stylesheet');
      UPDATE ${PREFIX}options SET option_value='Castuo Agritech' WHERE option_name='current_theme';
    " || true
  fi
fi

echo "Frontend disponible en: http://localhost:${FRONTEND_PORT}"
echo "Admin en: http://localhost:${FRONTEND_PORT}/wp-admin"

if [[ "$OPEN_BROWSER" == "true" ]]; then
  "$BROWSER" "http://localhost:${FRONTEND_PORT}" || true
  "$BROWSER" "http://localhost:${FRONTEND_PORT}/wp-admin" || true
fi
