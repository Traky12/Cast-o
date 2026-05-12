#!/usr/bin/env bash
set -euo pipefail

required=(
  secrets/vault_token
  secrets/iot_bearer
  secrets/wireless_logic_token
  secrets/mistral_key
  secrets/sabionda_key
)

required_env_vars=(
  HETZNER_API_KEY
  GAIACHAIN_API_KEY
  IPFS_API_KEY
  MISTRAL_API_KEY
  SABIONDA_API_KEY
  N8N_API_KEY
  N8N_PASSWORD
  JWT_SECRET_KEY
  WEBHOOK_URL
  GAIA_CHAIN_PRIVATE_KEY_FILE
)

for f in "${required[@]}"; do
  if [[ ! -s "$f" ]]; then
    echo "Missing or empty secret: $f" >&2
    exit 1
  fi
done

if [[ -f ".env" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      if [[ "$value" =~ ^\"(.*)\"$ ]]; then
        value="${BASH_REMATCH[1]}"
      elif [[ "$value" =~ ^\'(.*)\'$ ]]; then
        value="${BASH_REMATCH[1]}"
      fi
      printf -v "$key" '%s' "$value"
      export "$key"
    fi
  done < ".env"
fi

for key in "${required_env_vars[@]}"; do
  value="${!key:-}"
  if [[ -z "$value" || "$value" == "<CHANGE_ME>" || "$value" == "CHANGE_ME" ]]; then
    echo "Missing required .env value: $key" >&2
    exit 1
  fi
done

if [[ ! -f "${GAIA_CHAIN_PRIVATE_KEY_FILE}" ]]; then
  echo "GAIA key file not found: ${GAIA_CHAIN_PRIVATE_KEY_FILE}" >&2
  exit 1
fi

if find secrets -type f -perm /022 | grep -q .; then
  echo "Insecure permissions detected in secrets/ (group/other writable)" >&2
  find secrets -type f -perm /022 >&2
  exit 1
fi

critical_env_vars=(
  HETZNER_API_KEY
  GAIACHAIN_API_KEY
  IPFS_API_KEY
  MISTRAL_API_KEY
  SABIONDA_API_KEY
  N8N_API_KEY
  N8N_PASSWORD
  JWT_SECRET_KEY
  WEBHOOK_URL
  GAIA_CHAIN_PRIVATE_KEY_FILE
)

for env_file in .env .env.cloud; do
  [[ -f "$env_file" ]] || continue
  for key in "${critical_env_vars[@]}"; do
    line="$(grep -E "^${key}=" "$env_file" 2>/dev/null | head -n 1 || true)"
    [[ -z "$line" ]] && continue
    value="${line#*=}"
    if [[ "$value" == "<CHANGE_ME>" || "$value" == "CHANGE_ME" || "$value" == '"<CHANGE_ME>"' || "$value" == '"CHANGE_ME"' ]]; then
      echo "Placeholder detectado en variable critica ${key} de ${env_file}" >&2
      exit 1
    fi
  done
done

echo "All required secrets are present"
