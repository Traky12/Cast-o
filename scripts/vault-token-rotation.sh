#!/bin/bash
# Vault Token Rotation Script - Run via cron every 7 days

set -euo pipefail

VAULT_ADDR=${VAULT_ADDR:-https://vault.castuo.es}
VAULT_TOKEN=${VAULT_TOKEN}
ROTATION_INTERVAL=7  # Days

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"; }

log "Starting Vault token rotation..."

# 1. Check current token TTL
TTL=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
  -X GET "$VAULT_ADDR/v1/auth/token/lookup-self" | \
  jq -r '.data.ttl')

log "Current token TTL: $TTL seconds"

# 2. Create new token
NEW_TOKEN=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
  -X POST "$VAULT_ADDR/v1/auth/token/create" \
  -d '{"ttl":"720h", "policies":["default","castuo"]}' | \
  jq -r '.auth.client_token')

log "New token generated: ${NEW_TOKEN:0:20}..."

# 3. Update in all services
for service in fastapi n8n thingsdata; do
  docker exec "$service" bash -c "echo 'VAULT_TOKEN=$NEW_TOKEN' >> /etc/vault.env"
  docker restart "$service"
  log "Restarted service: $service"
done

# 4. Revoke old token after 1 hour grace period
sleep 3600
curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
  -X PUT "$VAULT_ADDR/v1/auth/token/revoke-self"

log "Old token revoked"
log "Token rotation completed successfully"
