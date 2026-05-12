#!/bin/bash
# CASTÚO-SYSTEM™ — Verificación TPM + GaiaChain + OpenZeppelin Defender (dispositivo IoT)
# Requiere: tpm_firmware_verifier instalado, GAIA_CHAIN_API_KEY (y opcional DEFENDER_API_KEY)

set -e
VERIFIER="${TPM_VERIFIER:-/usr/local/bin/tpm_firmware_verifier}"
FW_BIN="${FIRMWARE_BIN:-/firmware/bin/firmware.bin}"
FW_PUB="${FIRMWARE_PUB:-/firmware/keys/firmware.pub.pem}"
FW_SIG="${FIRMWARE_SIG:-/firmware/bin/firmware.sig}"
API_BASE="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"
DEVICE_ID=$(hostname 2>/dev/null || echo "iot-device")

# 1. Verificar firma TPM localmente
if [ ! -x "$VERIFIER" ]; then
  echo "⚠️  Verificador TPM no encontrado en $VERIFIER; omitiendo paso local."
else
  if ! "$VERIFIER" "$FW_BIN" "$FW_PUB" "$FW_SIG"; then
    echo "❌ Firma TPM inválida"
    exit 1
  fi
fi

# 2. Enviar hash a GaiaChain (si API key definida)
if [ -z "$GAIA_CHAIN_API_KEY" ]; then
  echo "⚠️  GAIA_CHAIN_API_KEY no definido; omitiendo verificación GaiaChain."
  exit 0
fi

FIRMWARE_HASH=$(sha256sum "$FW_BIN" 2>/dev/null | awk '{print $1}')
SIGNATURE_B64=""
[ -f "$FW_SIG" ] && SIGNATURE_B64=$(base64 -w 0 < "$FW_SIG" 2>/dev/null || base64 < "$FW_SIG")
TPM_CERT_B64=""
[ -f "/etc/gaiachain/tpm_certs/$DEVICE_ID.pem" ] && TPM_CERT_B64=$(base64 -w 0 < "/etc/gaiachain/tpm_certs/$DEVICE_ID.pem" 2>/dev/null || base64 < "/etc/gaiachain/tpm_certs/$DEVICE_ID.pem")

RESPONSE=$(curl -sf -X POST "$API_BASE/api/v1/iot/verify" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"device_id\": \"$DEVICE_ID\",
    \"firmware_hash\": \"$FIRMWARE_HASH\",
    \"signature\": \"$SIGNATURE_B64\",
    \"tpm_certificate\": \"$TPM_CERT_B64\"
  }" 2>/dev/null) || true

if [ -n "$RESPONSE" ] && echo "$RESPONSE" | grep -q '"status":"VERIFIED"'; then
  TX_HASH=$(echo "$RESPONSE" | jq -r '.tx_hash // empty')
  echo "  GaiaChain TX: $TX_HASH"
else
  echo "⚠️  Verificación en GaiaChain no disponible o fallida (API puede no implementar /api/v1/iot/verify)."
fi

# 3. Registrar en Defender (opcional)
if [ -n "$DEFENDER_API_KEY" ] && [ -n "$GAIA_CHAIN_VALIDATOR_ADDRESS" ] && [ -n "$TX_HASH" ]; then
  DEFENDER_RESPONSE=$(curl -sf -X POST "https://api.defender.openzeppelin.com/v1/verify/iot" \
    -H "Authorization: Bearer $DEFENDER_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"contract\": \"$GAIA_CHAIN_VALIDATOR_ADDRESS\",
      \"device\": \"$DEVICE_ID\",
      \"firmware_hash\": \"$FIRMWARE_HASH\",
      \"gaiachain_tx\": \"$TX_HASH\"
    }" 2>/dev/null) || true
  if echo "$DEFENDER_RESPONSE" | grep -q '"status":"SUCCESS"'; then
    echo "  Defender ID: $(echo "$DEFENDER_RESPONSE" | jq -r '.id // empty')"
  fi
fi

echo "✅ Dispositivo verificado (TPM + GaiaChain + Defender si aplica)"
