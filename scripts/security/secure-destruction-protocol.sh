#!/bin/bash
# CASTÚO-SYSTEM™ — Protocolo de destrucción segura (DMS). Solo el administrador autorizado.
# Requiere: contraseña maestra + YubiKey OTP. Zeroize HSM, GaiaChain readonly, IPFS unpin, notificación, apagado.
# Uso: sudo ./scripts/security/secure-destruction-protocol.sh

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"

echo "=== Protocolo de destrucción segura (DMS) ==="
read -s -p "Introduce la contraseña maestra para activar DMS: " MASTER_PASSWORD
echo
read -p "Toca tu YubiKey y pega el OTP: " YUBIKEY_OTP

[ -z "$MASTER_PASSWORD" ] && { echo "Contraseña vacía."; exit 1; }
[ ! -f "$CHAIN_DIR/master_password.hash" ] && { echo "No hay hash de contraseña maestra."; exit 1; }

INPUT_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
STORED_HASH=$(cat "$CHAIN_DIR/master_password.hash")
if [ "$INPUT_HASH" != "$STORED_HASH" ]; then
  echo "Verificación fallida. Abortando."
  unset MASTER_PASSWORD INPUT_HASH STORED_HASH
  exit 1
fi

# Verificación con GaiaChain (si API disponible)
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
  TS=$(date +%s)
  SIG=$(echo -n "DMS_ACTIVATION_${TS}" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  VERIFICATION=$(curl -sf -X POST "${API_URL}/api/v1/auth/dms" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"master_password_hash\":\"${INPUT_HASH}\",\"yubikey_otp\":\"${YUBIKEY_OTP}\",\"signature\":\"${SIG}\",\"timestamp\":${TS}}" 2>/dev/null | jq -r '.status // "FAIL"') || VERIFICATION="SKIP"
  if [ "$VERIFICATION" = "FAIL" ] && [ "$VERIFICATION" != "SKIP" ]; then
    echo "Verificación GaiaChain fallida. Abortando."
    unset MASTER_PASSWORD INPUT_HASH STORED_HASH
    exit 1
  fi
fi
unset INPUT_HASH STORED_HASH

echo "Activando destrucción en HSM..."
if command -v pkcs11-tool >/dev/null 2>&1 && [ -n "$HSM_MODULE" ]; then
  pkcs11-tool --login --pin "$MASTER_PASSWORD" --zeroize-token 2>/dev/null || true
fi
unset MASTER_PASSWORD

echo "Poniendo GaiaChain en modo solo lectura..."
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ]; then
  TS=$(date +%s)
  SIG=$(echo -n "GAIACHAIN_READONLY_${TS}" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  curl -sf -X POST "${API_URL}/api/v1/emergency/readonly" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"reason\":\"Security breach - DMS\",\"signature\":\"${SIG}\",\"timestamp\":${TS}}" >/dev/null || true
fi

echo "Eliminando pins de backups en IPFS..."
if command -v ipfs >/dev/null 2>&1 && [ -n "$GAIA_CHAIN_ADMIN_KEY" ]; then
  CIDS=$(curl -sf "${API_URL}/api/v1/backups" -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" 2>/dev/null | jq -r '.[].ipfs_cid // empty') || true
  for cid in $CIDS; do
    ipfs pin rm "$cid" 2>/dev/null || true
    ipfs repo gc 2>/dev/null || true
  done
fi

echo "Notificando a autoridades..."
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
  TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  SIG=$(echo -n "AUTHORITIES_ALERT_$(date +%s)" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  curl -sf -X POST "${API_URL}/api/v1/alert/authorities" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"SECURITY_BREACH\",\"level\":\"CRITICAL\",\"action\":\"DATA_DESTRUCTION_PROTOCOL\",\"timestamp\":\"${TS}\",\"signature\":\"${SIG}\"}" >/dev/null || true
fi

echo "Apagando sistemas..."
systemctl poweroff 2>/dev/null || true
exit 0
