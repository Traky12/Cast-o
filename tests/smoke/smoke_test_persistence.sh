#!/usr/bin/env bash
# PEI-002: validar que un envelope sobrevive a docker restart con volumen persistente.
# Uso: desde repo root, bash tests/smoke/smoke_test_persistence.sh
set -euo pipefail

TOKEN="${PEI002_STUB_BEARER_TOKEN:-test_token_smoke}"
IMAGE="${PEI002_STUB_IMAGE:-pei002-stub}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
API_DIR="$ROOT/pei-002-tracechain/api"
DATA_DIR="${PEI002_SMOKE_DATA:-$API_DIR/data}"
DOCKERFILE="$API_DIR/Dockerfile"

mkdir -p "$DATA_DIR"
docker rm -f pei002-smoke >/dev/null 2>&1 || true

echo "==> build $IMAGE"
docker build -t "$IMAGE" -f "$DOCKERFILE" "$API_DIR"

echo "==> run (volume $DATA_DIR -> /app/data)"
docker run -d --name pei002-smoke -p 8010:8010 \
  -e "PEI002_STUB_BEARER_TOKEN=$TOKEN" \
  -v "$DATA_DIR:/app/data" \
  "$IMAGE"

sleep 2

DIGEST="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
BODY="{\"event_type\":\"sigpac_validation\",\"digest\":\"$DIGEST\",\"timestamp\":1700000000,\"parcelas\":1,\"cumplen\":1,\"metadata\":{}}"

echo "==> POST /api/pei-002/envelope"
curl -sS -f -X POST "http://127.0.0.1:8010/api/pei-002/envelope" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$BODY" >/dev/null

echo "==> docker restart pei002-smoke"
docker restart pei002-smoke
sleep 2

echo "==> GET /api/pei-002/events/envelopes"
EVT="$(curl -sS -f -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:8010/api/pei-002/events/envelopes" | jq -r '.[0].payload.event_type // empty')"

if [[ "$EVT" != "sigpac_validation" ]]; then
  echo "FAIL: expected event_type sigpac_validation, got '$EVT'" >&2
  docker rm -f pei002-smoke >/dev/null 2>&1 || true
  exit 1
fi

echo "OK: persistencia verificada (event_type=$EVT)"

docker rm -f pei002-smoke >/dev/null 2>&1 || true
exit 0
