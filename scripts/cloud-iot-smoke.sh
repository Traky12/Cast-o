#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.cloud}"
COMPOSE_FILE="${2:-docker-compose.cloud.yml}"
TOPIC="${3:-castuo/sensors/smoke}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: env file not found: ${ENV_FILE}"
  exit 1
fi

set -a
# shellcheck disable=SC1090
. "${ENV_FILE}"
set +a

echo "Running IoT smoke test with ${COMPOSE_FILE} and ${ENV_FILE}"

docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" --profile iot up -d --build iot-bridge iot-processor

echo "Waiting bridge startup..."
sleep 4

SMOKE_PAYLOAD="$(python - <<'PY'
import json, time, uuid
print(json.dumps({
    "sensor_id": "smoke-sensor-01",
    "temperature": 22.7,
    "humidity": 58.4,
    "ts": int(time.time()),
    "smoke_id": str(uuid.uuid4())
}))
PY
)"

MQTT_USER="${WIRELESS_LOGIC_MQTT_USER:-}"
MQTT_PASS="${WIRELESS_LOGIC_MQTT_PASS:-}"

docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T iot-bridge sh -lc \
  "mosquitto_passwd -b -c /mosquitto/config/passwords '${MQTT_USER}' '${MQTT_PASS}' >/dev/null 2>&1 || true"

docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" exec -T iot-bridge sh -lc \
  "mosquitto_pub -h localhost -p 1883 -u '${MQTT_USER}' -P '${MQTT_PASS}' -t '${TOPIC}' -m '${SMOKE_PAYLOAD}'"

echo "Message published. Checking logs for ingest markers..."
sleep 4

LOGS="$(docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs --no-color --tail=100 iot-processor || true)"
echo "${LOGS}" | rg "POST .*IOT|POST .*TRACES|POST .*http" >/dev/null \
  && echo "GO: smoke publish -> ingest path observed in iot-processor logs." \
  || { echo "NO-GO: ingest markers not found in iot-processor logs."; exit 1; }
