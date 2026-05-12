#!/bin/bash
# CASTÚO-SYSTEM™ — Activa el protocolo de destrucción cuántica (simulación) y DMS clásico como respaldo.
# Requiere autenticación previa (biométrica o YubiKey + contraseña).
# Uso: ./scripts/security/activate_quantum_destruction.sh [target]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASTUO_ROOT="${CASTUO_ROOT:-/opt/castuo}"
TARGET="${1:-caceres_quantum_dc}"

# 1. Autenticación
if [ -f "$SCRIPT_DIR/biometric_auth.py" ]; then
  python3 "$SCRIPT_DIR/biometric_auth.py" || { echo "Autenticación fallida."; exit 1; }
elif [ -f "$SCRIPT_DIR/authenticate_with_yubikey.py" ]; then
  python3 "$SCRIPT_DIR/authenticate_with_yubikey.py" || { echo "Autenticación fallida."; exit 1; }
else
  echo "Configure GAIA_CHAIN_ADMIN_KEY y opcionalmente ejecute authenticate o biometric_auth antes."
fi

# 2. Destrucción cuántica: con QKD si está configurado, si no simulador
export CASTUO_QUANTUM_TRIGGER_DMS=0
if [ -n "$QKD_SERVER_ADDRESS" ] && [ -f "$SCRIPT_DIR/quantum_destruction_qkd.py" ]; then
  python3 "$SCRIPT_DIR/quantum_destruction_qkd.py" activate "$TARGET" || true
else
  python3 "$SCRIPT_DIR/quantum_destruction_simulator.py" simulate "$TARGET" || true
fi

# 3. Activar DMS clásico como respaldo (solo si se confirma)
read -p "¿Activar DMS clásico como respaldo? (yes/NO): " CONFIRM
if [ "$CONFIRM" = "yes" ]; then
  [ -x "$SCRIPT_DIR/secure-destruction-protocol.sh" ] && "$SCRIPT_DIR/secure-destruction-protocol.sh" || true
fi

# 4. Notificación a GaiaChain
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" ]; then
  SIG=$(echo -n "QUANTUM_ALERT_$(date +%s)" | openssl dgst -sha512 -sign "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" 2>/dev/null | base64 -w0) || true
  curl -sf -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/quantum_alert" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"QUANTUM_DESTRUCTION_ACTIVATED\",\"target\":\"$TARGET\",\"trigger\":\"simulated_quantum_threat\",\"fallback_actions\":[\"DMS_CLASSIC\",\"GAIACHAIN_READONLY\"],\"signature\":\"$SIG\"}" >/dev/null || true
fi

echo "Protocolo de destrucción cuántica (simulación) ejecutado. DMS clásico disponible como respaldo."
