#!/usr/bin/env bash
# Demo ingest continuo (ajustar host y frecuencia para no saturar el stand).
set -euo pipefail
BASE="${CASTUO_API:-http://127.0.0.1:8000}"
while true; do
  T=$((20 + RANDOM % 15))
  H=$((50 + RANDOM % 30))
  R=$((500 + RANDOM % 400))
  C=$((350 + RANDOM % 150))
  AT="agrovoltaico"
  case $((RANDOM % 3)) in
    0) AT="hidroponico" ;;
    1) AT="medicinal" ;;
  esac
  curl -sS -X POST "${BASE}/agents/gemelo/ingest" \
    -H "Content-Type: application/json" \
    -d "{\"agent_type\":\"${AT}\",\"sensor_data\":{\"temperature\":${T},\"humidity\":${H},\"radiation\":${R},\"co2\":${C}}}" \
    | head -c 200
  echo
  sleep "${DEMO_INTERVAL_SEC:-2}"
done
