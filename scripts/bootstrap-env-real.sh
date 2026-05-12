#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env"
BASE_FILE=".env.example"
CLOUD_FILE=".env.cloud"

usage() {
  cat <<'EOF'
Uso: scripts/bootstrap-env-real.sh [opciones]

Opciones:
  --env-file <ruta>     Archivo de salida .env (default: .env)
  --force               Sobrescribe claves existentes en .env
  -h, --help            Mostrar ayuda

Notas:
- No imprime secretos.
- Prioriza valores de .env.cloud y archivos en secrets/.
EOF
}

FORCE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --force)
      FORCE=1
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

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$BASE_FILE" "$ENV_FILE"
  chmod 600 "$ENV_FILE" || true
fi

tmp_env="$(mktemp)"
cp "$ENV_FILE" "$tmp_env"

set_kv() {
  local key="$1"
  local value="$2"
  [[ -z "$value" ]] && return 0

  local current
  current="$(grep -E "^${key}=" "$tmp_env" 2>/dev/null | head -n 1 | cut -d= -f2- || true)"

  if [[ "$FORCE" -eq 0 ]]; then
    if [[ -n "$current" && "$current" != "<CHANGE_ME>" ]]; then
      return 0
    fi
  fi

  if grep -qE "^${key}=" "$tmp_env"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$tmp_env"
  else
    echo "${key}=${value}" >> "$tmp_env"
  fi
}

read_secret_file() {
  local path="$1"
  if [[ -s "$path" ]]; then
    tr -d '\r\n' < "$path"
  fi
}

# 1) Cargar variables útiles de .env.cloud (sin sobreescribir si ya están bien)
if [[ -f "$CLOUD_FILE" ]]; then
  while IFS='=' read -r k v; do
    [[ -z "$k" ]] && continue
    [[ "$k" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [[ -z "${v:-}" ]] && continue
    set_kv "$k" "$v"
  done < <(awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=/{print $1"="$2}' "$CLOUD_FILE")
fi

# 2) Completar secretos desde ficheros locales seguros
mistral_key="$(read_secret_file secrets/mistral_key || true)"
sabionda_key="$(read_secret_file secrets/sabionda_key || true)"
vault_token_path="${ROOT_DIR}/secrets/vault_token"
iot_bearer_path="${ROOT_DIR}/secrets/iot_bearer"
gaia_key_path="${ROOT_DIR}/secrets/gaia_chain_private_key"
wireless_logic_token="$(read_secret_file secrets/wireless_logic_token || true)"

set_kv MISTRAL_API_KEY "$mistral_key"
set_kv SABIONDA_API_KEY "$sabionda_key"
set_kv N8N_PASSWORD "${N8N_PASSWORD:-}"
set_kv WEBHOOK_URL "${WEBHOOK_URL:-}"
set_kv LORAWAN_API_KEY "$wireless_logic_token"

[[ -f "$vault_token_path" ]] && set_kv VAULT_TOKEN_FILE "$vault_token_path"
[[ -f "$iot_bearer_path" ]] && set_kv CASTUO_IOT_BEARER_FILE "$iot_bearer_path"
[[ -f "secrets/sabionda_key" ]] && set_kv CASTUO_SABIONDA_API_KEY_FILE "${ROOT_DIR}/secrets/sabionda_key"
[[ -f "$gaia_key_path" ]] && set_kv GAIA_CHAIN_PRIVATE_KEY_FILE "$gaia_key_path"

# 3) Generar secretos locales seguros cuando estén vacíos
gen_if_missing() {
  local key="$1"
  local bytes="$2"
  local cur
  cur="$(grep -E "^${key}=" "$tmp_env" 2>/dev/null | head -n 1 | cut -d= -f2- || true)"
  if [[ -z "$cur" || "$cur" == "<CHANGE_ME>" ]]; then
    set_kv "$key" "$(openssl rand -hex "$bytes")"
  fi
}

gen_if_missing JWT_SECRET_KEY 32
gen_if_missing N8N_API_KEY 24

mv "$tmp_env" "$ENV_FILE"
chmod 600 "$ENV_FILE" || true

echo "[OK] .env actualizado en $ENV_FILE"
echo "[INFO] Verifica faltantes reales con: bash scripts/validate_hub_connectivity.sh --env-file $ENV_FILE --strict --check-endpoints"
