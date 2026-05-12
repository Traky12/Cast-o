#!/bin/bash
# CASTÚO-SYSTEM™ — Activa el protocolo de destrucción fotónica cuántica.
# Requiere autenticación previa (biométrica o YubiKey).
# Uso: ./scripts/security/activate_photonic_destruction.sh [target]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-madrid_quantum_dc}"

# 1. Autenticación
if [ -f "$SCRIPT_DIR/biometric_auth.py" ]; then
  python3 "$SCRIPT_DIR/biometric_auth.py" || { echo "Autenticación fallida."; exit 1; }
elif [ -f "$SCRIPT_DIR/authenticate_with_yubikey.py" ]; then
  python3 "$SCRIPT_DIR/authenticate_with_yubikey.py" || { echo "Autenticación fallida."; exit 1; }
fi

# 2. Activar destrucción fotónica
export CASTUO_PHOTONIC_TRIGGER_DMS=0
python3 "$SCRIPT_DIR/quantum_photonic_destruction.py" activate "$TARGET" || true

# 3. Notificación GaiaChain
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" ]; then
  SIG=$(echo -n "PHOTONIC_ALERT_$(date +%s)" | openssl dgst -sha512 -sign "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" 2>/dev/null | base64 -w0) || true
  curl -sf -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/quantum_photonic_alert" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"QUANTUM_PHOTONIC_DESTRUCTION_ACTIVATED\",\"target\":\"$TARGET\",\"trigger\":\"photonic_hardware\",\"fallback_actions\":[\"DMS_CLASSIC\",\"GAIACHAIN_READONLY\"],\"signature\":\"$SIG\"}" >/dev/null || true
fi

echo "Protocolo de destrucción fotónica cuántica ejecutado. DMS disponible como respaldo."
