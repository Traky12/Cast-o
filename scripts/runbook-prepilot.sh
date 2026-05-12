#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +"%Y%m%d-%H%M%S")"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/artifacts/prepilot/$STAMP}"
HETZNER_IP="${HETZNER_IP:-}"
PUBLIC_API_HEALTH_URL="${PUBLIC_API_HEALTH_URL:-https://api.castuo-system.cloud/health}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
LOCAL_API_HEALTH_URL="${LOCAL_API_HEALTH_URL:-http://localhost:8000/health}"
STRICT=false
SKIP_START=false
SKIP_K8S=false

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
  cat <<EOF
Uso: $0 [opciones]

Opciones:
  --ip <IPv4/host>     Ejecuta checks remotos de Hetzner (ssh/nc)
  --output-dir <dir>   Directorio de evidencias (default: artifacts/prepilot/<timestamp>)
  --strict             Devuelve exit code 1 si hay WARN/FAIL
  --skip-start         No ejecuta scripts/start_all_services.sh
  --skip-k8s           Omite checks de Kubernetes/TLS cert-manager
  -h, --help           Mostrar ayuda
EOF
}

info() { echo -e "${YELLOW}[INFO]${NC} $*"; }
ok() { echo -e "${GREEN}[PASS]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; }

record_pass() { PASS_COUNT=$((PASS_COUNT + 1)); }
record_warn() { WARN_COUNT=$((WARN_COUNT + 1)); }
record_fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); }

run_capture() {
  local title="$1"
  local cmd="$2"
  local out_file="$3"

  {
    echo "# $title"
    echo "# CMD: $cmd"
    echo "# UTC: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo
    bash -lc "$cmd"
  } >"$out_file" 2>&1
}

check_cmd() {
  local title="$1"
  local cmd="$2"
  local out_file="$3"

  if run_capture "$title" "$cmd" "$out_file"; then
    ok "$title"
    record_pass
    return 0
  fi

  warn "$title"
  record_warn
  return 0
}

check_critical() {
  local title="$1"
  local cmd="$2"
  local out_file="$3"

  if run_capture "$title" "$cmd" "$out_file"; then
    ok "$title"
    record_pass
    return 0
  fi

  fail "$title"
  record_fail
  return 0
}

require_optional_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    warn "Comando no disponible: $cmd"
    record_warn
    return 1
  fi
  return 0
}

find_mqtt_container() {
  docker ps --format '{{.Names}}' | grep -E '(castuo-mqtt|mosquitto|mqtt|castuo-mqtt-bridge)' | head -n1 || true
}

find_redis_container() {
  docker ps --format '{{.Names}}' | grep -E '(^redis$|redis|castuo-redis)' | head -n1 || true
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --ip)
        HETZNER_IP="${2:-}"
        shift 2
        ;;
      --output-dir)
        OUTPUT_DIR="${2:-}"
        shift 2
        ;;
      --strict)
        STRICT=true
        shift
        ;;
      --skip-start)
        SKIP_START=true
        shift
        ;;
      --skip-k8s)
        SKIP_K8S=true
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        echo "Argumento no soportado: $1" >&2
        usage
        exit 2
        ;;
    esac
  done
}

main() {
  parse_args "$@"

  mkdir -p "$OUTPUT_DIR"
  info "Evidencias en: $OUTPUT_DIR"

  # 1) Infraestructura remota (si se provee IP)
  if [[ -n "$HETZNER_IP" ]]; then
    check_critical "Servidor Hetzner accesible por SSH" \
      "ssh -o BatchMode=yes -o ConnectTimeout=8 root@$HETZNER_IP 'hostname && uptime'" \
      "$OUTPUT_DIR/01_hetzner_server.txt"

    check_critical "Puertos remotos accesibles" \
      "nc -zv $HETZNER_IP 22 80 443 8000 5678 3000 9090 8545" \
      "$OUTPUT_DIR/01_hetzner_server.txt"
  else
    info "Sin --ip: se omiten checks remotos de Hetzner"
    {
      echo "Sin --ip: checks SSH y puertos omitidos"
      echo "Definir HETZNER_IP para validacion remota"
    } >"$OUTPUT_DIR/01_hetzner_server.txt"
  fi

  # 2) Prerrequisitos locales
  check_critical "Docker instalado" "docker --version" "$OUTPUT_DIR/02_docker_status.txt"

  if command -v docker-compose >/dev/null 2>&1; then
    check_cmd "Docker Compose v1/v2 disponible" "docker-compose --version" "$OUTPUT_DIR/02_docker_status.txt"
  else
    check_cmd "Docker Compose plugin disponible" "docker compose version" "$OUTPUT_DIR/02_docker_status.txt"
  fi

  # 3) Arranque recomendado
  if [[ "$SKIP_START" == false ]]; then
    check_critical "Arranque de stack recomendado" \
      "bash '$ROOT_DIR/scripts/start_all_services.sh'" \
      "$OUTPUT_DIR/90_start_all_services.txt"
  else
    info "--skip-start habilitado: se omite arranque de servicios"
  fi

  # 4) Verificacion integral existente
  check_critical "Verificacion operativa integral" \
    "bash '$ROOT_DIR/scripts/verify_operational_stack.sh'" \
    "$OUTPUT_DIR/91_verify_operational_stack.txt"

  # 5) Contenedores y salud
  check_critical "Contenedores castuo en running" \
    "docker ps --filter 'name=castuo' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" \
    "$OUTPUT_DIR/03_containers_running.txt"

  check_critical "API health responde" \
    "for i in {1..12}; do curl -fsS '$LOCAL_API_HEALTH_URL' && exit 0; sleep 5; done; exit 1" \
    "$OUTPUT_DIR/04_api_health.txt"

  check_cmd "Prometheus healthy" \
    "for i in {1..8}; do curl -fsS '$PROMETHEUS_URL/-/healthy' && exit 0; sleep 3; done; exit 1" \
    "$OUTPUT_DIR/10_prometheus_metrics.txt"

  check_cmd "Grafana health endpoint" \
    "curl -fsS -I '$GRAFANA_URL/api/health'" \
    "$OUTPUT_DIR/11_grafana_dashboards.txt"

  check_cmd "Grafana dashboards visibles" \
    "code=$(curl -s -o /tmp/grafana_dash.json -w '%{http_code}' '$GRAFANA_URL/api/dashboards/db' || true); cat /tmp/grafana_dash.json; [[ \"\$code\" == \"200\" || \"\$code\" == \"401\" || \"\$code\" == \"403\" ]]" \
    "$OUTPUT_DIR/11_grafana_dashboards.txt"

  # 6) MQTT pub/sub real
  MQTT_CONTAINER="$(find_mqtt_container)"
  if [[ -n "$MQTT_CONTAINER" ]]; then
    check_cmd "MQTT publica y consume mensaje de prueba" \
      "docker exec '$MQTT_CONTAINER' sh -lc \"mosquitto_pub -h localhost -t castuo/prepilot/ping -m '{\\\"status\\\":\\\"ok\\\"}' -q 1 && mosquitto_sub -h localhost -t castuo/prepilot/ping -C 1 -W 3\"" \
      "$OUTPUT_DIR/05_mqtt_status.txt"
  else
    warn "No se detecto contenedor MQTT"
    record_warn
    echo "No se detecto contenedor MQTT" >"$OUTPUT_DIR/05_mqtt_status.txt"
  fi

  REDIS_CONTAINER="$(find_redis_container)"
  if command -v redis-cli >/dev/null 2>&1; then
    check_cmd "Redis responde PONG" \
      "redis-cli ping" \
      "$OUTPUT_DIR/06_redis_ping.txt"
  elif [[ -n "$REDIS_CONTAINER" ]]; then
    check_cmd "Redis responde PONG (contenedor)" \
      "docker exec '$REDIS_CONTAINER' redis-cli ping" \
      "$OUTPUT_DIR/06_redis_ping.txt"
  else
    warn "No se detecto cliente/contenedor Redis"
    record_warn
    echo "No se detecto cliente/contenedor Redis" >"$OUTPUT_DIR/06_redis_ping.txt"
  fi

  # 7) Persistencia
  DB_ROOT_PASSWORD="${WP_DB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-castuo_root}}"

  check_critical "MariaDB SHOW DATABASES" \
    "docker exec castuo-mariadb mariadb -uroot -p'$DB_ROOT_PASSWORD' -e 'SHOW DATABASES;'" \
    "$OUTPUT_DIR/07_mariadb_schemas.txt"

  check_critical "Schema castuo_system con tablas criticas" \
    "docker exec castuo-mariadb mariadb -uroot -p'$DB_ROOT_PASSWORD' -e 'USE castuo_system; SHOW TABLES;'" \
    "$OUTPUT_DIR/07_mariadb_schemas.txt"

  check_cmd "Upsert usuario piloto" \
    "docker exec castuo-mariadb mariadb -uroot -p'$DB_ROOT_PASSWORD' -e \"USE castuo_system; INSERT INTO users (user_uid, email, role, full_name) VALUES ('pilot-user-001', 'piloto@castuo-system.cloud', 'admin', 'Usuario Piloto') ON DUPLICATE KEY UPDATE email='piloto@castuo-system.cloud', role='admin', full_name='Usuario Piloto';\"" \
    "$OUTPUT_DIR/92_pilot_user_upsert.txt"

  check_cmd "Consulta usuario piloto" \
    "docker exec castuo-mariadb mariadb -uroot -p'$DB_ROOT_PASSWORD' -e \"USE castuo_system; SELECT user_uid,email,role,full_name FROM users WHERE user_uid='pilot-user-001';\"" \
    "$OUTPUT_DIR/93_pilot_user_select.txt"

  # 8) Secretos sin exponer valores
  if [[ -f "$ROOT_DIR/.env" ]]; then
    check_cmd "Variables criticas definidas (sin imprimir valores)" \
      "for k in JWT_SECRET_KEY POSTGRES_PASSWORD N8N_PASSWORD SABIONDA_API_KEY MISTRAL_API_KEY GRAFANA_PASSWORD; do grep -Eq \"^\$k=[^<].+\" '$ROOT_DIR/.env' || exit 1; done; echo 'Variables presentes y no vacias'" \
      "$OUTPUT_DIR/08_secrets_check.txt"
  else
    warn "No existe .env en raiz"
    record_warn
    echo ".env no encontrado" >"$OUTPUT_DIR/08_secrets_check.txt"
  fi

  check_cmd "TLS endpoint publico responde" \
    "curl -fsS -I '$PUBLIC_API_HEALTH_URL'" \
    "$OUTPUT_DIR/09_tls_certificates.txt"

  # 9) K8s/TLS opcional
  if [[ "$SKIP_K8S" == false ]] && command -v kubectl >/dev/null 2>&1; then
    check_cmd "kubectl cluster-info" \
      "kubectl cluster-info" \
      "$OUTPUT_DIR/17_k8s_cluster_info.txt"

    check_cmd "cert-manager emitiendo certificados" \
      "kubectl logs -n cert-manager deploy/cert-manager --tail 200 | grep -i 'Successfully issued certificate'" \
      "$OUTPUT_DIR/18_cert_manager_tls.txt"
  else
    info "Checks k8s/tls omitidos (sin kubectl o --skip-k8s)"
  fi

  # 10) Resumen Go/No-Go
  check_cmd "Telemetria IoT en topic castuo/#" \
    "if [ -n '$MQTT_CONTAINER' ]; then docker exec '$MQTT_CONTAINER' sh -lc \"mosquitto_pub -h localhost -t castuo/prepilot/telemetry -m '{\\\"status\\\":\\\"ok\\\"}' -q 1 && mosquitto_sub -h localhost -t 'castuo/#' -C 1 -W 5\"; else echo 'MQTT container no disponible'; exit 1; fi" \
    "$OUTPUT_DIR/12_iot_telemetry.txt"

  SUMMARY_FILE="$OUTPUT_DIR/00_summary.txt"
  {
    echo "Resumen de Verificaciones ($(date -u +"%Y-%m-%d %H:%M:%S UTC"))"
    echo "================================================="
    echo "PASS: $PASS_COUNT"
    echo "WARN: $WARN_COUNT"
    echo "FAIL: $FAIL_COUNT"
    echo
    if [[ "$FAIL_COUNT" -eq 0 ]]; then
      echo "GO_NO_GO: GO"
      echo "Motivo: no hay bloqueantes criticos"
    else
      echo "GO_NO_GO: NO-GO"
      echo "Motivo: existen bloqueantes criticos"
    fi
    echo
    echo "OUTPUT_DIR: $OUTPUT_DIR"
  } >"$SUMMARY_FILE"

  cat "$SUMMARY_FILE"

  if [[ "$FAIL_COUNT" -gt 0 ]]; then
    exit 1
  fi

  if [[ "$STRICT" == true && "$WARN_COUNT" -gt 0 ]]; then
    exit 1
  fi
}

main "$@"
