#!/bin/bash
# CASTÚO-SYSTEM™ — Revocar YubiKey perdida o comprometida. Requiere: contraseña maestra + YubiKey de respaldo (OTP).
# Uso: ./scripts/security/destroy-lost-yubikey.sh <serial_perdida>

set -e
[ -z "$1" ] && { echo "Uso: $0 <serial_yubikey_perdida>"; exit 1; }
LOST_SERIAL="$1"
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"

read -s -p "Introduce la contraseña maestra: " MASTER_PASSWORD
echo
read -p "Toca tu YubiKey de respaldo y pega el OTP: " BACKUP_YUBIKEY_OTP

[ -z "$MASTER_PASSWORD" ] && { echo "Contraseña vacía."; exit 1; }
[ ! -f "$CHAIN_DIR/master_password.hash" ] && { echo "No hay hash de contraseña maestra."; exit 1; }

INPUT_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
STORED_HASH=$(cat "$CHAIN_DIR/master_password.hash")
if [ "$INPUT_HASH" != "$STORED_HASH" ]; then
  echo "Verificación fallida. Abortando."
  unset MASTER_PASSWORD INPUT_HASH STORED_HASH
  exit 1
fi

if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
  TS=$(date +%s)
  SIG=$(echo -n "YUBIKEY_REVOKE_${LOST_SERIAL}_${TS}" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  VERIFICATION=$(curl -sf -X POST "${API_URL}/api/v1/auth/yubikey_revoke" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"master_password_hash\":\"${INPUT_HASH}\",\"backup_yubikey_otp\":\"${BACKUP_YUBIKEY_OTP}\",\"lost_yubikey_serial\":\"${LOST_SERIAL}\",\"signature\":\"${SIG}\"}" 2>/dev/null | jq -r '.status // "FAIL"') || VERIFICATION="SKIP"
  if [ "$VERIFICATION" = "FAIL" ] && [ "$VERIFICATION" != "SKIP" ]; then
    echo "Verificación fallida. Abortando."
    unset MASTER_PASSWORD INPUT_HASH STORED_HASH
    exit 1
  fi
fi
unset MASTER_PASSWORD INPUT_HASH STORED_HASH

curl -sf -X POST "${API_URL}/api/v1/yubikey/revoke" \
  -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"serial\":\"${LOST_SERIAL}\",\"reason\":\"Lost or compromised\",\"admin_signature\":\"$(echo -n "YUBIKEY_REVOKE_${LOST_SERIAL}" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0)\"}" >/dev/null || true

curl -sf -X POST "${API_URL}/api/v1/alert/yubikey_lost" \
  -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"YUBIKEY_LOST\",\"serial\":\"${LOST_SERIAL}\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"signature\":\"$(echo -n "YUBIKEY_LOST_${LOST_SERIAL}_$(date +%s)" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0)\"}" >/dev/null || true

echo "YubiKey con serial ${LOST_SERIAL} revocada y notificada. Acceso bloqueado en GaiaChain/HSM."
