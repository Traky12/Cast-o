#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_PORT="${FRONTEND_PORT:-8083}"
WP_DB_ROOT_PASSWORD="${WP_DB_ROOT_PASSWORD:-castuo_root}"

log_info() { echo "[INFO] $*"; }
log_ok() { echo "[OK] $*"; }
log_warn() { echo "[WARN] $*"; }

compose_cmd() {
  if command -v docker >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

log_info "Iniciando procesos críticos CASTUO-SYSTEM..."
log_info "Frontend en puerto: ${FRONTEND_PORT}"

# 1) Frontend WordPress + MariaDB hardened
log_info "1/7 Iniciando frontend local hardened (WordPress + MariaDB)..."
FRONTEND_PORT="$FRONTEND_PORT" WP_DB_ROOT_PASSWORD="$WP_DB_ROOT_PASSWORD" bash "$ROOT_DIR/scripts/start_frontend_8003.sh" || {
  log_warn "No se pudo iniciar frontend con start_frontend_8003.sh"
}

# 2) Redis (cache)
log_info "2/7 Iniciando Redis..."
compose_cmd -f "$ROOT_DIR/docker-compose.microservices.yml" up -d redis || log_warn "Redis no inició"

# 3) MQTT broker
log_info "3/7 Iniciando MQTT broker..."
compose_cmd -f "$ROOT_DIR/docker-compose.iot.yml" up -d mosquitto || log_warn "Mosquitto no inició"

# 4) Backend API
log_info "4/7 Iniciando backend API..."
compose_cmd -f "$ROOT_DIR/docker-compose.microservices.yml" up -d api || log_warn "API no inició"

# 5) Prometheus
log_info "5/7 Iniciando Prometheus..."
compose_cmd -f "$ROOT_DIR/docker-compose.microservices.yml" up -d prometheus || log_warn "Prometheus no inició"

# 6) Grafana
log_info "6/7 Iniciando Grafana..."
compose_cmd -f "$ROOT_DIR/docker-compose.microservices.yml" up -d grafana || log_warn "Grafana no inició"

# 7) Inicialización de persistencia de negocio
log_info "7/7 Inicializando persistencia castuo_system..."
WP_DB_ROOT_PASSWORD="$WP_DB_ROOT_PASSWORD" bash "$ROOT_DIR/scripts/init_castuo_persistence.sh" || log_warn "Persistencia no inicializada automáticamente"

log_ok "Arranque recomendado completado."
echo "Comando recomendado de verificación: bash $ROOT_DIR/scripts/verify_operational_stack.sh"
