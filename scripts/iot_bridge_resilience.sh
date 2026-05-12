#!/usr/bin/env bash
set -euo pipefail

MAX_RETRIES=${MAX_RETRIES:-5}
SLEEP=${SLEEP:-2}

for ((i=1; i<=MAX_RETRIES; i++)); do
  if python services/iot/mqtt_bridge.py; then
    exit 0
  fi
  echo "iot-bridge failed (attempt $i/$MAX_RETRIES), retrying in ${SLEEP}s" >&2
  sleep "$SLEEP"
  SLEEP=$((SLEEP*2))
done

echo "DLQ fallback: persisting failed payload marker to /tmp/iot-dlq.log" >&2
date -u >> /tmp/iot-dlq.log
exit 1
