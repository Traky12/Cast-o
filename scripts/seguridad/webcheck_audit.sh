#!/usr/bin/env bash
# webcheck_audit.sh — Ejecución self-hosted y air-gap-safe del auditor de superficie
set -euo pipefail

TARGET="${WEBCHECK_TARGET:-127.0.0.1}"
AIRGAP="${BUNKER_AIRGAP:-false}"

if [[ "${AIRGAP}" == "true" ]]; then
  echo "[WebCheck] BUNKER_AIRGAP=true → Skip de auditoría (air-gap)."
  exit 0
fi

CONTAINER_NAME="${WEBCHECK_CONTAINER_NAME:-castuo-webcheck}"
IMAGE="${WEBCHECK_IMAGE:-lissy93/web-check}"
PORT="${WEBCHECK_PORT:-3000}"

cleanup() {
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[WebCheck] Levantando contenedor ${IMAGE}..."
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
docker run -d --name "${CONTAINER_NAME}" -p "${PORT}:3000" "${IMAGE}" >/dev/null

echo "[WebCheck] Esperando disponibilidad..."
for _ in {1..30}; do
  if curl -fs "http://localhost:${PORT}" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "[WebCheck] Ejecutando check contra target='${TARGET}'..."
REPORT="$(curl -fsS -G "http://localhost:${PORT}/api/check" --data-urlencode "target=${TARGET}" || true)"

if [[ -z "${REPORT}" ]]; then
  REPORT='{"status":"error","message":"No report returned"}'
fi

echo "${REPORT}" > webcheck_report.json
echo "[WebCheck] Report guardado: webcheck_report.json"

