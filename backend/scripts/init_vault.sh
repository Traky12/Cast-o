#!/usr/bin/env bash
# backend/scripts/init_vault.sh
# Inicialización de HashiCorp Vault OSS (EU/OSS).
# Dev: export VAULT_ADDR=http://127.0.0.1:8200; VAULT_TOKEN=root-token ./scripts/init_vault.sh
# Producción: vault operator init -key-shares=5 -key-threshold=3; guardar claves; unseal con 3 claves.

set -e
export VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
export VAULT_TOKEN="${VAULT_TOKEN:-root-token}"

echo "=== Inicializando Vault en $VAULT_ADDR ==="

# Esperar a que Vault responda
until vault status 2>/dev/null; do
  echo "Esperando a que Vault esté listo..."
  sleep 1
done

# Si está sellado, en producción desbloquear con: vault operator unseal <key1> <key2> <key3>
if vault status 2>/dev/null | grep -q "Sealed.*true"; then
  echo "Vault está sellado. En producción ejecutar: vault operator unseal <key1>; vault operator unseal <key2>; vault operator unseal <key3>"
  exit 1
fi

vault login "$VAULT_TOKEN" 2>/dev/null || true

# Habilitar KV v2, Transit y PQC (si disponible)
vault secrets enable -path=secret kv-v2 2>/dev/null || true
vault secrets enable transit 2>/dev/null || true
vault secrets enable -path=pqc transit 2>/dev/null || true

# Claves Transit para rotación
for key in consent_signing_key K_backend_consent K_gaiachain_sign K_media_engine K_jwt_signing; do
  vault write -f transit/keys/"$key" type=rsa-2048 2>/dev/null || true
done

# Política para backend (incluye key_rotation y PQC)
cat > /tmp/backend-policy.hcl <<'EOL'
path "secret/data/consent_service" {
  capabilities = ["read"]
}
path "secret/data/key_rotation/*" {
  capabilities = ["read", "create", "update"]
}
path "transit/keys/*" {
  capabilities = ["create", "read", "update", "delete", "rotate"]
}
path "transit/encrypt/*" {
  capabilities = ["update"]
}
path "transit/decrypt/*" {
  capabilities = ["update"]
}
path "transit/sign/*" {
  capabilities = ["update"]
}
path "transit/verify/*" {
  capabilities = ["update"]
}
path "pqc/keys/*" {
  capabilities = ["create", "read", "update", "delete", "rotate"]
}
path "sys/seal" {
  capabilities = ["update"]
}
path "sys/unseal" {
  capabilities = ["update"]
}
EOL
vault policy write backend /tmp/backend-policy.hcl 2>/dev/null || true

# Secretos de ejemplo (desarrollo)
vault kv put secret/consent_service \
  gaiachain_private_key="dev-gaiachain-key" \
  ipfs_api_key="dev-ipfs-key" \
  jwt_signing_key="dev-jwt-key" 2>/dev/null || true

echo "=== Vault configurado ==="
echo "Ejemplo producción: vault kv put secret/consent_service gaiachain_private_key=... ipfs_api_key=... jwt_signing_key=..."
