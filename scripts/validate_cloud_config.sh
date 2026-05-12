#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_vars=(
  POSTGRES_PASSWORD
  N8N_PASSWORD
  ALLOWED_ORIGINS
  VAULT_ADDR
  VAULT_TOKEN_FILE
  CASTUO_SABIONDA_API_KEY_FILE
  CASTUO_IOT_BEARER_FILE
)

missing=()
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    missing+=("$var")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "Missing required vars: ${missing[*]}" >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  docker compose -f docker-compose.cloud.yml config >/dev/null
  echo "docker-compose.cloud.yml is valid"
else
  echo "docker command not available; skipped compose validation"
fi

echo "Cloud config validation OK"
