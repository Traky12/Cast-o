#!/usr/bin/env bash
# Verificación post-deploy CASTÚO-SYSTEM (ejecutar en el VPS, raíz del repo).
#
# Uso:
#   chmod +x deploy/verify_stack.sh
#   ./deploy/verify_stack.sh
#
# Variables opcionales:
#   COMPOSE_FILE=docker-compose.prod.yml   (por defecto)
#   ENV_FILE=.env.production               (por defecto)
#   PUBLIC_API_HEALTH_URL=https://api.tudominio.eu/health   (prueba vía nginx/TLS)
#   VERIFY_PROMETHEUS=1                    (falla si :9090 no responde; el prod por defecto no incluye Prometheus)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE=(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE")

fail=0

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[FAIL] No existe $COMPOSE_FILE (¿estás en la raíz del repo?)" >&2
  exit 1
fi
if [[ ! -f "$ENV_FILE" ]]; then
  echo "[FAIL] No existe $ENV_FILE" >&2
  exit 1
fi

extract_env() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'
}

PGUSER="$(extract_env POSTGRES_USER)"
PGDB="$(extract_env POSTGRES_DB)"
PGUSER="${PGUSER:-castuo}"
PGDB="${PGDB:-castuo}"

echo "== docker compose ps ($COMPOSE_FILE) =="
if ! "${COMPOSE[@]}" ps; then
  echo "[FAIL] docker compose ps" >&2
  exit 1
fi

echo "== API /health (contenedor api, puerto interno 8000) =="
if "${COMPOSE[@]}" exec -T api curl -fsS "http://127.0.0.1:8000/health" >/dev/null; then
  echo "[OK] api /health"
else
  echo "[FAIL] api /health (¿postgres sano y api arriba?)" >&2
  fail=1
fi

if [[ -n "${PUBLIC_API_HEALTH_URL:-}" ]]; then
  echo "== API /health (pública) ${PUBLIC_API_HEALTH_URL} =="
  if curl -fsS "$PUBLIC_API_HEALTH_URL" >/dev/null; then
    echo "[OK] health pública"
  else
    echo "[FAIL] health pública" >&2
    fail=1
  fi
fi

echo "== PostgreSQL tablas hydroponics_* (usuario=${PGUSER}, db=${PGDB}) =="
hydro_count="$("${COMPOSE[@]}" exec -T postgres psql -U "$PGUSER" -d "$PGDB" -t -A -c \
  "SELECT count(*)::text FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'hydroponics_%';" 2>/dev/null | tr -d '[:space:]' || echo "0")"
if [[ "${hydro_count:-0}" =~ ^[0-9]+$ ]] && [[ "${hydro_count}" -ge 1 ]]; then
  echo "[OK] ${hydro_count} tabla(s) hydroponics_*"
  "${COMPOSE[@]}" exec -T postgres psql -U "$PGUSER" -d "$PGDB" -c '\dt hydroponics_*' || true
else
  echo "[FAIL] Sin tablas hydroponics_* — en volumen antiguo ejecuta:" >&2
  echo "  ${COMPOSE[*]} exec -T postgres psql -U $PGUSER -d $PGDB -f /docker-entrypoint-initdb.d/002_hydroponics_saas.sql" >&2
  fail=1
fi

if [[ "${VERIFY_PROMETHEUS:-0}" == "1" ]]; then
  echo "== Prometheus http://127.0.0.1:9090/targets =="
  if curl -fsS "http://127.0.0.1:9090/targets" >/dev/null; then
    echo "[OK] Prometheus responde"
  else
    echo "[FAIL] Prometheus no accesible en :9090" >&2
    fail=1
  fi
else
  echo "[SKIP] Prometheus (el compose prod del repo no lo incluye por defecto; VERIFY_PROMETHEUS=1 para exigir :9090)"
fi

if [[ "${fail:-0}" -ne 0 ]]; then
  echo "== Resultado: FALLÓ al menos una comprobación crítica ==" >&2
  exit 1
fi
echo "== Resultado: OK =="
