#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env"
STRICT=0
CHECK_ENDPOINTS=0

usage() {
  cat <<'EOF'
Uso: scripts/validate_hub_connectivity.sh [opciones]

Opciones:
  --env-file <ruta>      Archivo .env a cargar (default: .env)
  --strict               Falla si falta cualquier variable/secret requerido
  --check-endpoints      Intenta health-check HTTP de endpoints declarados
  -h, --help             Mostrar ayuda

Notas:
- No imprime secretos.
- En modo no estricto, reporta WARN y termina 0 para facilitar diagnostico inicial.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --strict)
      STRICT=1
      shift
      ;;
    --check-endpoints)
      CHECK_ENDPOINTS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Parametro no reconocido: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      # Remover comillas envolventes simples o dobles si existen.
      if [[ "$value" =~ ^\"(.*)\"$ ]]; then
        value="${BASH_REMATCH[1]}"
      elif [[ "$value" =~ ^\'(.*)\'$ ]]; then
        value="${BASH_REMATCH[1]}"
      fi
      printf -v "$key" '%s' "$value"
      export "$key"
    fi
  done < "$ENV_FILE"
fi

missing=0

check_var() {
  local name="$1"
  local value="${!name:-}"
  if [[ -z "$value" || "$value" == "<CHANGE_ME>" || "$value" == "CHANGE_ME" ]]; then
    echo "WARN var faltante: $name"
    missing=1
  else
    echo "OK   var: $name"
  fi
}

check_file_secret() {
  local name="$1"
  local path="${!name:-}"
  if [[ -z "$path" ]]; then
    echo "WARN secret file var faltante: $name"
    missing=1
    return
  fi
  if [[ ! -s "$path" ]]; then
    echo "WARN secret file no disponible: $name -> $path"
    missing=1
  else
    echo "OK   secret file: $name"
  fi
}

health_url_from_base() {
  local base="$1"
  if [[ "$base" =~ /api/v1/?$ ]]; then
    echo "${base%/}/health"
  else
    echo "${base%/}/health"
  fi
}

check_http_health() {
  local label="$1"
  local raw_url="$2"
  if [[ -z "$raw_url" || "$raw_url" == "<CHANGE_ME>" ]]; then
    echo "WARN endpoint $label no configurado"
    missing=1
    return
  fi
  local url
  url="$(health_url_from_base "$raw_url")"
  if curl -fsS --max-time 8 "$url" >/dev/null 2>&1; then
    echo "OK   endpoint: $label -> $url"
  else
    echo "WARN endpoint no responde: $label -> $url"
    missing=1
  fi
}

echo "== Validacion Hub CASTUO-SYSTEM =="
echo "Env file: $ENV_FILE"

# Claves para integracion transversal IA + orquestacion + infra
check_var MISTRAL_API_KEY
check_var SABIONDA_API_KEY
check_var N8N_API_KEY
check_var HETZNER_API_KEY
check_var GAIACHAIN_API_KEY
check_var IPFS_API_KEY
check_var N8N_PASSWORD
check_var JWT_SECRET_KEY
check_var WEBHOOK_URL

# Patron recomendado por ficheros secretos
check_file_secret VAULT_TOKEN_FILE
check_file_secret CASTUO_SABIONDA_API_KEY_FILE
check_file_secret CASTUO_IOT_BEARER_FILE
check_file_secret GAIA_CHAIN_PRIVATE_KEY_FILE

if [[ "$CHECK_ENDPOINTS" -eq 1 ]]; then
  echo "== Verificando endpoints =="
  check_http_health "Mistral" "${MISTRAL_ENDPOINT:-https://api.mistral.ai/v1}"
  check_http_health "Sabionda" "${SABIONDA_ENDPOINT:-http://sabionda-core:6000/api/v1}"
  check_http_health "n8n" "${N8N_ENDPOINT:-http://n8n-main:5678}"
  check_http_health "TRACES" "${TRACES_API_URL:-}"
fi

if [[ "$missing" -eq 1 ]]; then
  if [[ "$STRICT" -eq 1 ]]; then
    echo "NO-GO: faltan dependencias de conectividad hub" >&2
    exit 1
  fi
  echo "WARN: hay faltantes, revisar docs/ci-policies.md y docs/ops/HUB-CONNECTIVIDAD.md"
  exit 0
fi

echo "GO: conectividad base del hub validada"
