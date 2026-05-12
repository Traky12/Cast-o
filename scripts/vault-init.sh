#!/bin/bash
# scripts/vault-init.sh - Initialize Vault with production policies and auth methods

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-castuo-root-token-2026}"

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"; }

log "Initializing Vault..."

# Function to retry Vault operations
vault_api() {
  local method=$1
  local path=$2
  local data=$3
  
  curl -s -X "$method" \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d "$data" \
    "$VAULT_ADDR/v1/$path"
}

# 1. Enable KV Secrets Engine (v2)
log "Enabling KV Secrets Engine v2..."
vault_api POST sys/mounts/secret '{"type":"kv","options":{"version":"2"}}' || true

# 2. Create policies
log "Creating policies..."

# Policy for FastAPI
cat > /tmp/fastapi-policy.hcl << 'EOF'
path "secret/data/castuo/database/*" {
  capabilities = ["read", "list"]
}

path "secret/data/castuo/aws/*" {
  capabilities = ["read"]
}

path "secret/data/castuo/jwt/*" {
  capabilities = ["read"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

vault_api PUT sys/policies/acl/fastapi "$(jq -R -s . < /tmp/fastapi-policy.hcl)" || true

# Policy for n8n
cat > /tmp/n8n-policy.hcl << 'EOF'
path "secret/data/castuo/thingsdata/*" {
  capabilities = ["read", "list"]
}

path "secret/data/castuo/mqtt/*" {
  capabilities = ["read"]
}

path "secret/data/castuo/kafka/*" {
  capabilities = ["read"]
}
EOF

vault_api PUT sys/policies/acl/n8n "$(jq -R -s . < /tmp/n8n-policy.hcl)" || true

# 3. Enable AppRole auth method
log "Enabling AppRole auth method..."
vault_api POST sys/auth/approle '{"type":"approle"}' || true

# 4. Create AppRole for FastAPI
log "Creating AppRole for FastAPI..."
vault_api POST auth/approle/role/fastapi '{"policies":["fastapi"],"token_ttl":"1h","token_max_ttl":"4h"}' || true

# 5. Generate Role ID and Secret ID
log "Generating FastAPI credentials..."
ROLE_ID=$(vault_api GET auth/approle/role/fastapi/role-id | jq -r '.data.role_id')
SECRET_ID=$(vault_api POST auth/approle/role/fastapi/secret-id '' | jq -r '.data.secret_id')

log "FastAPI Role ID: $ROLE_ID"
log "FastAPI Secret ID: $SECRET_ID (save this securely!)"

# 6. Store initial secrets
log "Storing initial secrets..."
vault_api POST secret/data/castuo/database/primary '{"data":{"username":"castuo_iot","password":"generated-password-123","host":"timescaledb","port":"5432","database":"castuo_telemetry"}}' || true

vault_api POST secret/data/castuo/jwt/signing '{"data":{"key":"your-jwt-secret-key-here","algorithm":"HS256"}}' || true

vault_api POST secret/data/castuo/aws/credentials '{"data":{"access_key":"","secret_key":"","region":"eu-west-1"}}' || true

# 7. Enable audit logging
log "Enabling audit logging..."
vault_api POST sys/audit/file '{"type":"file","options":{"file_path":"/vault/logs/audit.log"}}' || true

log "Vault initialization completed"
log "Next steps:"
log "  1. Save Role ID and Secret ID in secure location"
log "  2. Configure environment variables in services"
log "  3. Set up automated token rotation"
