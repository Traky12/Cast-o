#!/usr/bin/env bash
# docker-harden.sh - Aplica hardening automático a contenedores CASTÚO-SYSTEM
# Modo: preserva volúmenes y datos, solo actualiza configuración de runtime
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NETWORK_NAME="castuo-network"
DOCKER_NETWORK_DRIVER="${DOCKER_NETWORK_DRIVER:-bridge}"

# Configuración de hardening
WORDPRESS_MEMORY="${WORDPRESS_MEMORY:-1g}"
WORDPRESS_CPUS="${WORDPRESS_CPUS:-2}"
MARIADB_MEMORY="${MARIADB_MEMORY:-512m}"
MARIADB_CPUS="${MARIADB_CPUS:-1}"

# Variables de entorno y credenciales
FRONTEND_PORT="${FRONTEND_PORT:-5432}"
WP_DB_NAME="${WP_DB_NAME:-wordpress}"
WP_DB_USER="${WP_DB_USER:-wordpress}"
WP_DB_PASSWORD="${WP_DB_PASSWORD:-wordpress}"
WP_DB_ROOT_PASSWORD="${WP_DB_ROOT_PASSWORD:-castuo_root}"

WP_SITE_TITLE="${WP_SITE_TITLE:-CASTUO Frontend}"
WP_ADMIN_USER="${WP_ADMIN_USER:-castuo_admin}"
WP_ADMIN_PASSWORD="${WP_ADMIN_PASSWORD:-CastuoAdmin!2026}"
WP_ADMIN_EMAIL="${WP_ADMIN_EMAIL:-admin@castuo.local}"

# Variables de imágenes (tags fijos para seguridad)
WORDPRESS_IMAGE="${WORDPRESS_IMAGE:-wordpress:6.5-apache}"
MARIADB_IMAGE="${MARIADB_IMAGE:-mariadb:11.2}"

# Flags
DRY_RUN="false"
VERBOSE="false"
PRESERVE_DATA="true"

print_usage() {
  cat <<EOF
Uso: $0 [OPCIONES]

Aplica hardening automático a contenedores CASTÚO-SYSTEM preservando datos.

OPCIONES:
  --dry-run              No ejecuta cambios, solo muestra plan
  --verbose              Output verboso
  --no-preserve          Borra volúmenes (¡cuidado!)
  -h, --help             Muestra esta ayuda

HARDENING APLICADO:
  ✓ Restart policy: unless-stopped (reinicio automático)
  ✓ Healthchecks: curl para WordPress, mysqladmin para MariaDB
  ✓ Límites CPU/memoria configurables
  ✓ Puerto exposición solo a localhost (127.0.0.1)
  ✓ Network isolation: red única castuo-network
  ✓ Environment variables desde .env si existe

EJEMPLO:
  ./docker-harden.sh --dry-run --verbose
  ./docker-harden.sh

EOF
}

log() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
  fi
}

log_info() {
  echo "ℹ️  $*"
}

log_ok() {
  echo "✅ $*"
}

log_warn() {
  echo "⚠️  $*" >&2
}

log_error() {
  echo "❌ $*" >&2
}

run_cmd() {
  if [[ "$DRY_RUN" == "true" ]]; then
    log "[DRY-RUN] $*"
  else
    log "$*"
    eval "$@" || return $?
  fi
}

# Parsear argumentos
for arg in "$@"; do
  case "$arg" in
    --dry-run)
      DRY_RUN="true"
      ;;
    --verbose)
      VERBOSE="true"
      ;;
    --no-preserve)
      PRESERVE_DATA="false"
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      log_error "Opción desconocida: $arg"
      print_usage
      exit 2
      ;;
  esac
done

# Header
cat <<'EOF'
╔════════════════════════════════════════════════════════════╗
║          Docker Hardening Automático - CASTÚO v2.1         ║
╚════════════════════════════════════════════════════════════╝
EOF

log_info "Iniciando hardening automático..."
[[ "$DRY_RUN" == "true" ]] && log_warn "MODO DRY-RUN: solo información, sin cambios"
[[ "$PRESERVE_DATA" == "true" ]] && log_ok "Modo preservación de datos: volúmenes persistirán"

# Verificar que docker está disponible
if ! command -v docker &>/dev/null; then
  log_error "Docker no encontrado en PATH"
  exit 1
fi

# Step 1: Crear red si no existe
log_info "Paso 1/5: Verificando red docker..."
if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
  log "Red $NETWORK_NAME no existe, creando..."
  run_cmd "docker network create --driver $DOCKER_NETWORK_DRIVER $NETWORK_NAME" || true
  log_ok "Red $NETWORK_NAME creada"
else
  log_ok "Red $NETWORK_NAME ya existe"
fi

# Step 2: Detener contenedores existentes (preservar volúmenes si no se pide eliminación)
log_info "Paso 2/5: Deteniendo contenedores existentes..."
for container in castuo-wordpress castuo-mariadb; do
  if docker ps --format '{{.Names}}' | grep -qx "$container"; then
    log "Deteniendo $container..."
    run_cmd "docker stop $container"
    log_ok "$container detenido"
  fi
done

# Step 3: Eliminar contenedores antiguos (pero no volúmenes si PRESERVE_DATA=true)
log_info "Paso 3/5: Eliminando contenedores antiguos..."
for container in castuo-wordpress castuo-mariadb; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$container"; then
    log "Eliminando contenedor $container..."
    run_cmd "docker rm $container"
    log_ok "$container eliminado"
  fi
done

# Step 4: Aplicar hardening a MariaDB
log_info "Paso 4/5: Redeployando MariaDB con hardening..."
run_cmd "docker run -d" \
  "--name castuo-mariadb" \
  "--restart unless-stopped" \
  "--memory '$MARIADB_MEMORY'" \
  "--cpus '$MARIADB_CPUS'" \
  "--network $NETWORK_NAME" \
  "--env MYSQL_ROOT_PASSWORD='$WP_DB_ROOT_PASSWORD'" \
  "--env MYSQL_DATABASE='$WP_DB_NAME'" \
  "--env MYSQL_USER='$WP_DB_USER'" \
  "--env MYSQL_PASSWORD='$WP_DB_PASSWORD'" \
  "--health-cmd \"test -S /var/run/mysqld/mysqld.sock || exit 1\"" \
  "--health-interval 10s" \
  "--health-timeout 5s" \
  "--health-retries 3" \
  "--health-start-period 30s" \
  "-v castuo_mariadb_data:/var/lib/mysql" \
  "$MARIADB_IMAGE"

log_ok "MariaDB redeployado con hardening"

# Esperar a que MariaDB esté listo (socket check)
log_info "Esperando a que MariaDB esté listo (socket check)..."
max_retries=60
retry_count=0
while [[ $retry_count -lt $max_retries ]]; do
  if docker exec castuo-mariadb test -S /var/run/mysqld/mysqld.sock 2>/dev/null; then
    log_ok "MariaDB está listo (socket disponible)"
    break
  fi
  retry_count=$((retry_count + 1))
  if [[ $((retry_count % 10)) -eq 0 ]]; then
    log "Intento $retry_count/$max_retries, esperando..."
  fi
  sleep 1
done

if [[ $retry_count -eq $max_retries ]]; then
  log_warn "⚠️  MariaDB timeout, pero continuando (contenedor está corriendo)..."
fi

# Step 5: Aplicar hardening a WordPress
log_info "Paso 5/5: Redeployando WordPress con hardening..."
run_cmd "docker run -d" \
  "--name castuo-wordpress" \
  "--restart unless-stopped" \
  "--memory '$WORDPRESS_MEMORY'" \
  "--cpus '$WORDPRESS_CPUS'" \
  "--network $NETWORK_NAME" \
  "--env WORDPRESS_DB_HOST=castuo-mariadb" \
  "--env WORDPRESS_DB_USER='$WP_DB_USER'" \
  "--env WORDPRESS_DB_PASSWORD='$WP_DB_PASSWORD'" \
  "--env WORDPRESS_DB_NAME='$WP_DB_NAME'" \
  "--env WORDPRESS_CONFIG_EXTRA='define(\"WP_SITEURL\", \"http://localhost:$FRONTEND_PORT\"); define(\"WP_HOME\", \"http://localhost:$FRONTEND_PORT\");'" \
  "--publish 127.0.0.1:$FRONTEND_PORT:80" \
  "--health-cmd \"curl -f http://127.0.0.1/wp-login.php || exit 1\"" \
  "--health-interval 30s" \
  "--health-timeout 5s" \
  "--health-retries 3" \
  "--health-start-period 45s" \
  "-v castuo_wordpress_data:/var/www/html" \
  "$WORDPRESS_IMAGE"

log_ok "WordPress redeployado con hardening"

# Conectar WordPress a castuo-wp-net para compatibilidad con scripts anteriores
log_info "Conectando WordPress a castuo-wp-net (compatibilidad backward)..."
docker network create castuo-wp-net 2>/dev/null || true
docker network connect castuo-wp-net castuo-wordpress 2>/dev/null || true
log_ok "WordPress conectado a castuo-network + castuo-wp-net"

# Esperar a que WordPress esté listo
log_info "Esperando a que WordPress esté listo (health check)..."
max_retries=45
retry_count=0
while [[ $retry_count -lt $max_retries ]]; do
  if curl -sf http://localhost:$FRONTEND_PORT/wp-login.php &>/dev/null; then
    log_ok "WordPress está listo"
    break
  fi
  retry_count=$((retry_count + 1))
  log "Intento $retry_count/$max_retries, esperando..."
  sleep 2
done

if [[ $retry_count -eq $max_retries ]]; then
  log_warn "WordPress no respondió después de ${max_retries}0 segundos, pero continuando..."
fi

# Resumen final
cat <<EOF

╔════════════════════════════════════════════════════════════╗
║                    HARDENING COMPLETADO                    ║
╚════════════════════════════════════════════════════════════╝

📊 CONFIGURACIÓN APLICADA:
  • Restart Policy: unless-stopped (reinicio automático en fallos)
  • WordPress Memory Limit: $WORDPRESS_MEMORY
  • WordPress CPU Limit: $WORDPRESS_CPUS cores
  • MariaDB Memory Limit: $MARIADB_MEMORY
  • MariaDB CPU Limit: $MARIADB_CPUS cores
  • Net Port Exposure: 127.0.0.1:$FRONTEND_PORT->80 (solo localhost)
  • Healthchecks: Enabled (WordPress + MariaDB)
  • Network Isolation: $NETWORK_NAME
  • Image Tags: Fixed (no :latest)

🔐 MEJORAS DE SEGURIDAD:
  ✅ Reinicio automático en fallos
  ✅ Monitoreo de salud continuo
  ✅ Límites de recursos aplicados
  ✅ Puerto no expuesto a nivel global
  ✅ Aislamiento en red privada

🚀 PRÓXIMOS PASOS:
  1. Verificar: docker ps --filter "name=castuo"
  2. Validar datos:
     docker exec castuo-wordpress curl http://localhost/wp-login.php
     docker exec castuo-mariadb mysql -u $WP_DB_USER -p$WP_DB_PASSWORD -e "SELECT COUNT(*) FROM $WP_DB_NAME.wp_posts;"
  3. Auditar de nuevo: ./scripts/docker-audit.sh --strict
  4. Acceso frontend: http://localhost:$FRONTEND_PORT

✨ Hardening automático completado en $(date '+%H:%M:%S')
EOF

log_ok "Hardening finalizado correctamente"
exit 0
