#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
ENDPOINT="${ENDPOINT:-/api/v1/skills/validar_lote}"
JWT_SECRET="${JWT_SECRET:-}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-}"
SKIP_HEALTHCHECK="${SKIP_HEALTHCHECK:-0}"
LOTE_ID="${LOTE_ID:-LOTE-$(date +%Y%m%d-%H%M%S)}"
EXPLORER_API_URL="${EXPLORER_API_URL:-https://explorer.gaiachain.cloud/api}"

if [[ -z "${JWT_SECRET}" && -n "${JWT_SECRET_KEY}" ]]; then
  JWT_SECRET="${JWT_SECRET_KEY}"
fi

if [[ -z "${JWT_SECRET}" ]]; then
  echo "[ERROR] Debes definir JWT_SECRET o JWT_SECRET_KEY" >&2
  exit 1
fi

for cmd in curl python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Comando requerido no encontrado: $cmd" >&2
    exit 1
  fi
done

json_pretty() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  else
    python3 -m json.tool
  fi
}

json_get() {
  local key="$1"
  local input_file="$2"
  python3 - "$key" "$input_file" <<'PY'
import json
import sys

key = sys.argv[1]
input_file = sys.argv[2]
with open(input_file, "r", encoding="utf-8") as fh:
    obj = json.load(fh)
value = obj
for part in key.split('.'):
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break

if value is None:
    print("")
elif isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(str(value))
PY
}

discover_endpoint_from_openapi() {
  local openapi_tmp
  openapi_tmp=$(mktemp)
  if curl -fsS "${API_URL}/openapi.json" -o "$openapi_tmp" >/dev/null 2>&1; then
    local discovered
    discovered=$(python3 - "$openapi_tmp" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    schema = json.load(fh)

paths = schema.get("paths", {})
for path, spec in paths.items():
    post_spec = spec.get("post", {}) if isinstance(spec, dict) else {}
    if "validar_lote" in path and post_spec:
        print(path)
        break
PY
)
    rm -f "$openapi_tmp"
    if [[ -n "$discovered" ]]; then
      ENDPOINT="$discovered"
      echo "[INFO] Endpoint autodetectado desde OpenAPI: ${ENDPOINT}"
      return 0
    fi
  else
    rm -f "$openapi_tmp"
  fi
  return 1
}

if [[ "$SKIP_HEALTHCHECK" != "1" ]]; then
  echo "[INFO] Verificando salud API en ${API_URL}/health"
  health_code=$(curl -sS -o /dev/null -w "%{http_code}" "${API_URL}/health" || true)
  if [[ "$health_code" != "200" ]]; then
    echo "[ERROR] Healthcheck fallido. Codigo: $health_code" >&2
    exit 1
  fi
fi

if [[ -z "${ENDPOINT:-}" || "${ENDPOINT}" == "/api/v1/skills/validar_lote" ]]; then
  discover_endpoint_from_openapi || true
fi

echo "[INFO] Generando JWT de prueba (expira en 60 min)"
JWT_TOKEN=$(JWT_SECRET="$JWT_SECRET" python3 <<'PY'
import datetime
import jwt
import os

secret = os.environ["JWT_SECRET"]
payload = {
    "sub": "operador_e2e",
    "role": "editor",
  "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
}
print(jwt.encode(payload, secret, algorithm="HS256"))
PY
)

payload=$(cat <<JSON
{
  "lote_id": "${LOTE_ID}",
  "metadatos": {
    "humedad": 65.5,
    "thc": 0.18,
    "cbd": 12.3,
    "fecha_cosecha": "2026-03-15",
    "ubicacion": "Dehesa de Caceres, parcela 42"
  },
  "firma_digital": "${JWT_TOKEN}"
}
JSON
)

tmp_response=$(mktemp)
trap 'rm -f "$tmp_response"' EXIT

echo "[INFO] Ejecutando POST ${API_URL}${ENDPOINT}"
http_code=$(curl -sS -o "$tmp_response" -w "%{http_code}" \
  -X POST "${API_URL}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d "$payload")

if [[ "$http_code" == "404" ]]; then
  alt_endpoint=""
  if [[ "$ENDPOINT" == "/api/v1/skills/validar_lote" ]]; then
    alt_endpoint="/skills/validar_lote"
  elif [[ "$ENDPOINT" == "/skills/validar_lote" ]]; then
    alt_endpoint="/api/v1/skills/validar_lote"
  fi
  if [[ -n "$alt_endpoint" ]]; then
    echo "[WARN] Not Found en ${ENDPOINT}, reintentando ${alt_endpoint}"
    ENDPOINT="$alt_endpoint"
    http_code=$(curl -sS -o "$tmp_response" -w "%{http_code}" \
      -X POST "${API_URL}${ENDPOINT}" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${JWT_TOKEN}" \
      -d "$payload")
  fi
fi

if [[ "$http_code" != "200" ]]; then
  echo "[ERROR] Endpoint devolvio HTTP ${http_code}" >&2
  echo "[ERROR] URL usada: ${API_URL}${ENDPOINT}" >&2
  echo "[ERROR] Si persiste Not Found, revisa rutas en ${API_URL}/openapi.json" >&2
  cat "$tmp_response" | json_pretty
  exit 1
fi

echo "[INFO] Respuesta del endpoint"
cat "$tmp_response" | json_pretty

status_value=$(json_get "status" "$tmp_response")
tx_hash=$(json_get "tx_hash" "$tmp_response")
qr_path=$(json_get "qr_path" "$tmp_response")
pdf_path=$(json_get "certificado_path" "$tmp_response")

if [[ "$status_value" != "OK" ]]; then
  echo "[ERROR] status no esperado: ${status_value}" >&2
  exit 1
fi

if [[ -z "$tx_hash" || -z "$qr_path" || -z "$pdf_path" ]]; then
  echo "[ERROR] Campos obligatorios ausentes en la respuesta" >&2
  exit 1
fi

echo "[INFO] Validando artefactos locales"
for artifact in "$qr_path" "$pdf_path"; do
  if [[ ! -f "$artifact" ]]; then
    echo "[ERROR] No existe artefacto: $artifact" >&2
    exit 1
  fi
  ls -lh "$artifact"
done

if command -v file >/dev/null 2>&1; then
  echo "[INFO] Tipo de archivo QR"
  file "$qr_path"
  echo "[INFO] Tipo de archivo PDF"
  file "$pdf_path"
fi

if [[ "$tx_hash" != sim-* ]]; then
  echo "[INFO] Verificando transaccion en explorer"
  curl -sS "${EXPLORER_API_URL}?module=transaction&action=gettxinfo&txhash=${tx_hash}" | json_pretty || true
else
  echo "[WARN] tx_hash simulado detectado (${tx_hash}). Revisar RPC/clave GaiaChain para on-chain real."
fi

echo "[OK] E2E completado para lote ${LOTE_ID}"
