#!/usr/bin/env bash
# cloud-iot-smoke.sh — thin wrapper that invokes cloud-iot-smoke.py
# Usage: ./scripts/cloud-iot-smoke.sh [--tls] [--api-url URL] [--mqtt-host HOST]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Defaults (can be overridden via environment or flags)
: "${SMOKE_API_URL:=http://127.0.0.1:8000}"
: "${SMOKE_MQTT_HOST:=127.0.0.1}"
: "${SMOKE_MQTT_PORT:=1883}"
: "${SMOKE_TIMEOUT:=10}"
: "${SMOKE_TLS:=0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tls)            SMOKE_TLS=1; SMOKE_MQTT_PORT=8883; shift ;;
    --api-url)        SMOKE_API_URL="$2"; shift 2 ;;
    --mqtt-host)      SMOKE_MQTT_HOST="$2"; shift 2 ;;
    --mqtt-port)      SMOKE_MQTT_PORT="$2"; shift 2 ;;
    --bearer)         SMOKE_BEARER="$2"; shift 2 ;;
    --timeout)        SMOKE_TIMEOUT="$2"; shift 2 ;;
    *) echo "Unknown flag: $1" >&2; exit 2 ;;
  esac
done

export SMOKE_API_URL SMOKE_MQTT_HOST SMOKE_MQTT_PORT SMOKE_TLS SMOKE_TIMEOUT

exec python "$ROOT_DIR/scripts/cloud-iot-smoke.py"
