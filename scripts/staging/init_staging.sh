#!/usr/bin/env bash
# scripts/staging/init_staging.sh
# Inicializa Vault en staging (sin HSM): init, unseal, habilitar secretos y políticas.
# Ejecutar desde la raíz del repo, con vault accesible (p.ej. port-forward o desde host con vault CLI).
# Uso: ./scripts/staging/init_staging.sh [VAULT_ADDR]
# Si no se pasa VAULT_ADDR, se usa http://127.0.0.1:8200 (port-forward: kubectl port-forward svc/vault 8200:8200).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VAULT_ADDR="${1:-http://127.0.0.1:8200}"
export VAULT_ADDR

echo "=== Staging: inicializando Vault en $VAULT_ADDR ==="

# Esperar a que Vault responda
until vault status -address="$VAULT_ADDR" 2>/dev/null; do
  echo "Esperando a que Vault esté listo..."
  sleep 2
done

# Si ya está inicializado y unsealed, solo habilitar secretos
if vault status -address="$VAULT_ADDR" 2>/dev/null | grep -q "Initialized.*true"; then
  if vault status -address="$VAULT_ADDR" 2>/dev/null | grep -q "Sealed.*false"; then
    echo "Vault ya inicializado y desbloqueado. Habilitando motores..."
    vault secrets enable -path=secret kv-v2 2>/dev/null || true
    vault secrets enable transit 2>/dev/null || true
    vault secrets enable -path=pqc transit 2>/dev/null || true
    echo "Listo. Para rotación y backend usa VAULT_TOKEN del .env.staging."
    exit 0
  fi
  echo "Vault está sellado. Desbloquear con: vault operator unseal <key1>; vault operator unseal <key2>; vault operator unseal <key3>"
  echo "Las claves están en vault_init.json (generado en el primer init)."
  exit 1
fi

# Inicializar (5 shares, threshold 3)
echo "Inicializando Vault (5/3 Shamir)..."
vault operator init -key-shares=5 -key-threshold=3 -format=json > "$ROOT_DIR/vault_init.json" || true
if [[ ! -f "$ROOT_DIR/vault_init.json" ]]; then
  echo "Error: no se pudo generar vault_init.json"
  exit 1
fi

# Unseal con las 3 primeras claves (requiere jq)
if command -v jq &>/dev/null; then
  for i in 0 1 2; do
    key=$(jq -r ".unseal_keys_b64[$i]" "$ROOT_DIR/vault_init.json")
    vault operator unseal "$key"
  done
else
  echo "Instale jq y ejecute manualmente: vault operator unseal \$(jq -r '.unseal_keys_b64[0]' vault_init.json); ..."
  exit 1
fi

# Login con root token y habilitar motores
root_token=$(jq -r .root_token "$ROOT_DIR/vault_init.json")
export VAULT_TOKEN="$root_token"
vault secrets enable -path=secret kv-v2 2>/dev/null || true
vault secrets enable transit 2>/dev/null || true
vault secrets enable -path=pqc transit 2>/dev/null || true

echo "Vault listo. Guarde vault_init.json en lugar seguro y configure VAULT_TOKEN en .env.staging con el root_token (o un token con políticas backend)."
echo "Luego: docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d backend auto-rotate"
