#!/bin/bash
# CASTÚO-SYSTEM™ — Registro del hash de clave maestra en GaiaChain (una vez)
# El hash debe generarse de forma segura (ej. desde verify-master-access o script que pida contraseña y no la guarde).

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
API_BASE="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"

if [ -n "$MASTER_KEY_HASH" ]; then
  HASH="$MASTER_KEY_HASH"
elif [ -f "$CHAIN_DIR/master_password.hash" ]; then
  HASH=$(cat "$CHAIN_DIR/master_password.hash")
else
  echo "Exporta MASTER_KEY_HASH o configura master_password.hash (ej. tras register-master-password.sh)."
  exit 1
fi

[ -z "$GAIA_CHAIN_ADMIN_KEY" ] && { echo "Exporta GAIA_CHAIN_ADMIN_KEY (ej. ejecutando verify-master-access.sh)."; exit 1; }

SIG=""
if [ -f "$CHAIN_DIR/master_key.pem" ]; then
  echo "Firma con master_key.pem requiere contraseña (no automatizable aquí)."
  echo "Opcional: firma manual y envía signature en el payload."
fi

curl -sf -X POST "$API_BASE/api/v1/master_key" \
  -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"master_key_hash\":\"$HASH\",\"signature\":\"$SIG\"}" || true
echo "Registro de clave maestra enviado a GaiaChain (si la API está disponible)."
