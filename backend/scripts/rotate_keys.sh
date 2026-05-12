#!/usr/bin/env bash
# backend/scripts/rotate_keys.sh
# Rotación de claves (Vault Transit + KV). EU/OSS – ISO 27001 A.10.1.2, GDPR Art. 32

set -e
export VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
export VAULT_TOKEN="${VAULT_TOKEN:-root-token}"

if [ -z "$VAULT_TOKEN" ]; then
  echo "Defina VAULT_TOKEN para rotar claves."
  exit 1
fi

echo "=== Rotación de claves Transit (consent_signing_key) ==="
vault write -f transit/keys/consent_signing_key/rotate 2>/dev/null || true
vault read transit/keys/consent_signing_key 2>/dev/null || true

echo "=== Recordatorio: rotar secretos en secret/consent_service manualmente ==="
echo "vault kv put secret/consent_service gaiachain_private_key=<nueva> ipfs_api_key=<nueva> jwt_signing_key=<nueva>"
echo "Reiniciar backend tras rotar secretos."
