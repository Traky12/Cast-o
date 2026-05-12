#!/usr/bin/env bash
set -euo pipefail

required=(
  secrets/vault_token
  secrets/iot_bearer
  secrets/wireless_logic_token
  secrets/mistral_key
  secrets/sabionda_key
)

for f in "${required[@]}"; do
  if [[ ! -s "$f" ]]; then
    echo "Missing or empty secret: $f" >&2
    exit 1
  fi
done

echo "All required secrets are present"
