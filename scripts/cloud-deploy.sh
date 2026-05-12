#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env.cloud"
PROFILES=()
ACTION="up"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --profile)
      PROFILES+=("$2")
      shift 2
      ;;
    --down)
      ACTION="down"
      shift
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

if [[ ${#PROFILES[@]} -eq 0 ]]; then
  PROFILES=(core iot ai observability)
fi

required_secrets=(vault_token iot_bearer mistral_key sabionda_key)
for profile in "${PROFILES[@]}"; do
  if [[ "$profile" == "iot" ]]; then
    required_secrets+=(wireless_logic_token)
  fi
done

for sec in "${required_secrets[@]}"; do
  if [[ ! -f "secrets/$sec" ]]; then
    echo "Missing required secret file: secrets/$sec" >&2
    exit 1
  fi
done

profiles_csv="$(IFS=,; echo "${PROFILES[*]}")"
python tests/cloud/cloud_validator.py --env-file "$ENV_FILE" --profiles "$profiles_csv"

profile_args=()
for p in "${PROFILES[@]}"; do
  profile_args+=(--profile "$p")
done

if [[ "$ACTION" == "down" ]]; then
  docker compose -f docker-compose.cloud.yml --env-file "$ENV_FILE" "${profile_args[@]}" down
  echo "Cloud overlay stopped"
  exit 0
fi

docker compose -f docker-compose.cloud.yml --env-file "$ENV_FILE" "${profile_args[@]}" up -d

echo "Waiting for API health endpoint..."
health_url="http://127.0.0.1:$(grep -E '^API_PORT=' "$ENV_FILE" | cut -d'=' -f2)/health"
for _ in {1..20}; do
  if curl -fsS "$health_url" >/dev/null 2>&1; then
    echo "GO: API health check passed at $health_url"
    exit 0
  fi
  sleep 2
done

echo "NO-GO: API health check failed at $health_url" >&2
exit 1
