#!/usr/bin/env bash
# Verificación producción CASTÚO (salud API vía contenedor, Postgres, métricas OT, opcional Prom/Grafana).
# Uso en VPS (raíz del repo):
#   chmod +x deploy/verify_production.sh
#   ./deploy/verify_production.sh
#
# Variables:
#   COMPOSE_FILE=docker-compose.prod.yml
#   ENV_FILE=.env.production
#   SKIP_PROMETHEUS=1   → no probar :9090
#   SKIP_GRAFANA=1      → no probar :3000
#   PUBLIC_API_HEALTH_URL=https://api.tudominio.eu/health
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
export ENV_FILE="${ENV_FILE:-.env.production}"

if [[ -x "./deploy/verify_stack.sh" ]]; then
  echo "=== verify_stack (API interno + hydro tablas) ==="
  ./deploy/verify_stack.sh || true
fi

COMPOSE=(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE")

echo "=== Panel Water/CTAEX /water-admin/ (desde contenedor api) ==="
if "${COMPOSE[@]}" exec -T api sh -c 'code=$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/water-admin/); echo "$code"; test "$code" = "200" || test "$code" = "301" || test "$code" = "307"' && echo "[OK] water-admin responde" || echo "[WARN] water-admin no 200/301/307 (¿imagen sin frontend/public?)"

echo "=== Métricas OT en /metrics (desde contenedor api) ==="
if "${COMPOSE[@]}" exec -T api sh -c 'curl -fsS http://127.0.0.1:8000/metrics' | grep -E '^(ot_|castuo_ot_)' | head -40 && echo "[OK] prefijos OT visibles" || echo "[WARN] no se encontraron métricas OT (¿Instrumentator?)"

echo "=== POST agrovoltaico (requiere tabla + X-API-KEY) ==="
KEY="${HYDROPONICS_TEST_KEY:-}"
if [[ -f "$ENV_FILE" ]]; then
  KEY=$(grep -E '^HYDROPONICS_SAAS_API_KEYS=' "$ENV_FILE" | head -1 | cut -d= -f2- | cut -d, -f1 | tr -d '\r')
fi
if [[ -n "$KEY" ]]; then
  if "${COMPOSE[@]}" exec -T api sh -c "curl -sS -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/agrovoltaic/observations -H 'Content-Type: application/json' -H 'X-API-KEY: $KEY' -d '{\"zone_id\":\"zone_cannabis_1\",\"irradiance_wm2\":800,\"shading_wm2\":120,\"source\":\"verify_production\"}'" | grep -qE '^(200|503)$' && echo "[OK] agrovoltaic POST (200 o 503 si sin tabla)" || echo "[WARN] agrovoltaic POST inesperado"
else
  echo "[SKIP] agrovoltaic: define HYDROPONICS_SAAS_API_KEYS en $ENV_FILE"
fi

if [[ "${SKIP_PROMETHEUS:-0}" != "1" ]]; then
  echo "=== Prometheus :9090/targets ==="
  curl -fsS "http://127.0.0.1:9090/targets" >/dev/null && echo "[OK] Prometheus" || echo "[SKIP/FAIL] Prometheus no en :9090 (normal si no está en compose prod)"
fi

if [[ "${SKIP_GRAFANA:-1}" != "1" ]]; then
  echo "=== Grafana :3000/api/health ==="
  curl -fsS "http://127.0.0.1:3000/api/health" >/dev/null && echo "[OK] Grafana" || echo "[SKIP/FAIL] Grafana"
fi

echo "=== Listo ==="
