#!/usr/bin/env bash
set -euo pipefail

pass_count=0
warn_count=0
STRICT=false

for arg in "$@"; do
  case "$arg" in
    --strict)
      STRICT=true
      ;;
    *)
      echo "[ERROR] Argumento no soportado: $arg" >&2
      echo "Uso: $0 [--strict]" >&2
      exit 2
      ;;
  esac
done

check_cmd() {
  local description="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "[PASS] $description"
    pass_count=$((pass_count + 1))
  else
    echo "[WARN] $description"
    warn_count=$((warn_count + 1))
  fi
}

check_http_ok() {
  local description="$1"
  local url="$2"
  local code
  code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
  if [[ "$code" =~ ^2|3 ]]; then
    echo "[PASS] $description (HTTP $code)"
    pass_count=$((pass_count + 1))
  else
    echo "[WARN] $description (HTTP $code)"
    warn_count=$((warn_count + 1))
  fi
}

echo "=== Verificación Operativa CASTUO-SYSTEM ==="

# 1) MariaDB persistencia
check_cmd "MariaDB corriendo" "docker ps --filter 'name=castuo-mariadb' --format '{{.Names}}' | grep -q castuo-mariadb"
check_cmd "Conexión MariaDB (SHOW DATABASES)" "docker exec castuo-mariadb mariadb -uroot -p\"${WP_DB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-castuo_root}}\" -e 'SHOW DATABASES;'"
check_cmd "Tablas críticas castuo_system" "docker exec castuo-mariadb mariadb -uroot -p\"${WP_DB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-castuo_root}}\" -e 'USE castuo_system; SHOW TABLES;'"

# 2) Backend FastAPI
check_cmd "Contenedor API corriendo" "docker ps --format '{{.Names}}' | grep -Eq '(^api$|api|sabionda-api)'"
check_http_ok "FastAPI /health responde" "http://localhost:8000/health"
check_cmd "FastAPI expone métricas" "curl -s http://localhost:8000/metrics | grep -q 'fastapi_requests_total'"

# 3) Frontend WordPress
check_cmd "Contenedor WordPress corriendo" "docker ps --filter 'name=castuo-wordpress' --format '{{.Names}}' | grep -q castuo-wordpress"
check_http_ok "Frontend /?pagename=sistema responde" "http://localhost:5432/?pagename=sistema"
check_cmd "Logs WordPress accesibles" "docker logs castuo-wordpress --tail 5"

# 4) MQTT
check_cmd "Contenedor Mosquitto corriendo" "docker ps --format '{{.Names}}' | grep -Eq '(mosquitto|mqtt|castuo-mqtt-bridge)'"
if command -v mosquitto_sub >/dev/null 2>&1; then
  check_cmd "Suscripción MQTT básica" "mosquitto_sub -h localhost -t 'castuo/sensors/#' -C 1 -W 2"
elif docker ps --format '{{.Names}}' | grep -Eq '(mosquitto|mqtt|castuo-mqtt-bridge)'; then
  mqtt_container="$(docker ps --format '{{.Names}}' | grep -E '(mosquitto|mqtt|castuo-mqtt-bridge)' | head -n1)"
  check_cmd "Suscripción MQTT básica (desde contenedor)" "docker exec \"$mqtt_container\" sh -c \"mosquitto_sub -h localhost -t castuo/health -C 1 -W 2\""
else
  echo "[WARN] mosquitto_sub no disponible en PATH (skip MQTT subscribe test)"
  warn_count=$((warn_count + 1))
fi

# 5) Redis
check_cmd "Contenedor Redis corriendo" "docker ps --format '{{.Names}}' | grep -Eq '(^redis$|redis)'"
if command -v redis-cli >/dev/null 2>&1; then
  check_cmd "Redis responde PONG" "redis-cli ping | grep -q PONG"
  check_cmd "Redis keys ejecuta" "redis-cli keys '*' >/dev/null"
elif docker ps --format '{{.Names}}' | grep -Eq '(^redis$|redis)'; then
  redis_container="$(docker ps --format '{{.Names}}' | grep -E '(^redis$|redis)' | head -n1)"
  check_cmd "Redis responde PONG (desde contenedor)" "docker exec \"$redis_container\" redis-cli ping | grep -q PONG"
  check_cmd "Redis keys ejecuta (desde contenedor)" "docker exec \"$redis_container\" redis-cli keys '*' >/dev/null"
else
  echo "[WARN] redis-cli no disponible en PATH (skip Redis CLI tests)"
  warn_count=$((warn_count + 1))
fi

# 6) Prometheus
check_cmd "Contenedor Prometheus corriendo" "docker ps --format '{{.Names}}' | grep -Eq '(prometheus|castuo-prometheus)'"
check_cmd "Prometheus query API responde" "curl -s 'http://localhost:9090/api/v1/query?query=up' | grep -q '\"status\":\"success\"'"

# 7) Grafana
check_cmd "Contenedor Grafana corriendo" "docker ps --format '{{.Names}}' | grep -Eq '(grafana|castuo-grafana)'"
check_http_ok "Grafana responde HTTP" "http://localhost:3000"

# 8) Cert-manager (si hay cluster)
if command -v kubectl >/dev/null 2>&1; then
  if kubectl cluster-info >/dev/null 2>&1; then
    check_cmd "Pods cert-manager en running" "kubectl get pods -n cert-manager --field-selector=status.phase=Running"
    check_cmd "Certificados castuo-system accesibles" "kubectl get certificate -n castuo-system"
    check_cmd "Challenges castuo-system accesibles" "kubectl get challenge -n castuo-system"
  else
    echo "[WARN] kubectl sin cluster activo (skip checks cert-manager)"
    warn_count=$((warn_count + 1))
  fi
else
  echo "[WARN] kubectl no disponible en PATH (skip checks cert-manager)"
  warn_count=$((warn_count + 1))
fi

echo
echo "Resumen: PASS=$pass_count WARN=$warn_count"
if [[ "$STRICT" == "true" && $warn_count -gt 0 ]]; then
  exit 1
fi
