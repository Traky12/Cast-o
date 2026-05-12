#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-staging}"
PROFILES_RAW="${2:-core,observability}"
ENV_FILE=".env.cloud"
COMPOSE_FILE="docker-compose.cloud.yml"
DRY_RUN="0"
ROLLBACK_ON_ERROR="0"
SKIP_HEALTHCHECK="0"
HEALTH_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    --rollback-on-error)
      ROLLBACK_ON_ERROR="1"
      shift
      ;;
    --skip-healthcheck)
      SKIP_HEALTHCHECK="1"
      shift
      ;;
    --health-url)
      HEALTH_URL="$2"
      shift 2
      ;;
    *)
      if [[ -z "${_POSITIONAL_ENV_SET:-}" ]]; then
        ENVIRONMENT="$1"
        _POSITIONAL_ENV_SET=1
      elif [[ -z "${_POSITIONAL_PROFILE_SET:-}" ]]; then
        PROFILES_RAW="$1"
        _POSITIONAL_PROFILE_SET=1
      else
        echo "ERROR: argumento no reconocido: $1"
        exit 1
      fi
      shift
      ;;
  esac
done

run_compose() {
  docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" "${PROFILE_ARGS[@]}" "$@"
}

rollback() {
  echo "Rolling back cloud stack..."
  run_compose down || true
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} no existe. Copia .env.cloud.example y rellena valores."
  exit 1
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "ERROR: ${COMPOSE_FILE} no existe."
  exit 1
fi

IFS=',' read -r -a PROFILES <<< "${PROFILES_RAW}"
PROFILE_ARGS=()
for profile in "${PROFILES[@]}"; do
  trimmed="$(echo "${profile}" | xargs)"
  [[ -n "${trimmed}" ]] && PROFILE_ARGS+=(--profile "${trimmed}")
done

echo "== CASTUO CLOUD DEPLOY =="
echo "Entorno: ${ENVIRONMENT}"
echo "Perfiles: ${PROFILES_RAW}"
echo "Compose: ${COMPOSE_FILE}"
echo "Env file: ${ENV_FILE}"
echo "Dry run: ${DRY_RUN}"

run_compose config >/dev/null
echo "Config OK"

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "Dry-run finalizado: no se aplicaron cambios."
  exit 0
fi

set +e
run_compose up -d --build
UP_EXIT=$?
set -e
if [[ ${UP_EXIT} -ne 0 ]]; then
  echo "ERROR: deploy fallido."
  [[ "${ROLLBACK_ON_ERROR}" == "1" ]] && rollback
  exit ${UP_EXIT}
fi

run_compose ps

if [[ "${SKIP_HEALTHCHECK}" == "1" ]]; then
  echo "Healthcheck omitido por flag."
  echo "Deploy completado."
  exit 0
fi

if [[ -z "${HEALTH_URL}" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
  HEALTH_URL="http://localhost:${API_PORT:-8000}${API_HEALTH_PATH:-/health}"
fi

echo "Healthcheck: ${HEALTH_URL}"
set +e
curl -fsS --max-time 10 "${HEALTH_URL}" >/dev/null
HC_EXIT=$?
set -e
if [[ ${HC_EXIT} -ne 0 ]]; then
  echo "ERROR: healthcheck fallido."
  [[ "${ROLLBACK_ON_ERROR}" == "1" ]] && rollback
  exit ${HC_EXIT}
fi

echo "Deploy completado y healthcheck OK."
