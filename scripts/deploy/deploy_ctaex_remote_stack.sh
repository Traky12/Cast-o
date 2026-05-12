#!/usr/bin/env bash
# Genera certificados TLS de laboratorio y levanta docker-compose/remote-access.yml
# Uso (desde la raíz del repo): bash scripts/deploy/deploy_ctaex_remote_stack.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CERT_DIR="$ROOT/docker/remote-access/nginx/certs"
ENV_FILE="${ENV_FILE:-$ROOT/.env.remote-access}"

mkdir -p "$CERT_DIR"

if [[ ! -f "$CERT_DIR/fullchain.pem" || ! -f "$CERT_DIR/privkey.pem" ]]; then
  echo "Generando certificado autofirmado en $CERT_DIR"
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" \
    -subj "/CN=castuo-remote-local"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Copia docker/remote-access/.env.remote-access.example a .env.remote-access y edita secretos."
  exit 1
fi

cd "$ROOT"
docker compose --env-file "$ENV_FILE" -f docker-compose/remote-access.yml up -d --build

echo "Keycloak (mapeado): http://localhost:\${KEYCLOAK_HOST_PORT:-8090}"
echo "API gateway directo: http://localhost:\${API_GATEWAY_PORT:-18000}/health"
echo "NGINX TLS: https://localhost:\${REMOTE_HTTPS_PORT:-8443}/health (curl -k)"
