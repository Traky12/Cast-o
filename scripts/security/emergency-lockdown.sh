#!/bin/bash
# CASTÚO-SYSTEM™ — Bloqueo total de emergencia (solo administrador autorizado)

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
[ ! -f "$CHAIN_DIR/master_password.hash" ] && { echo "No hay hash de contraseña maestra."; exit 1; }

read -s -p "Introduce la contraseña maestra para activar bloqueo total: " MASTER_PASSWORD
echo
INPUT_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
STORED_HASH=$(cat "$CHAIN_DIR/master_password.hash")
unset MASTER_PASSWORD
[ "$INPUT_HASH" != "$STORED_HASH" ] && { echo "Contraseña incorrecta."; exit 1; }

echo "Activando bloqueo total..."
systemctl stop gaiachain 2>/dev/null || true
systemctl stop suricata 2>/dev/null || true
systemctl stop wazuh-agent 2>/dev/null || true
ufw --force reset 2>/dev/null || true
ufw default deny incoming 2>/dev/null || true
ufw default deny outgoing 2>/dev/null || true
ufw allow out 53/udp 2>/dev/null || true
ufw allow out 123/udp 2>/dev/null || true
ufw --force enable 2>/dev/null || true

if [ -n "$GAIA_CHAIN_ADMIN_KEY" ]; then
  curl -sf -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/emergency" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" -H "Content-Type: application/json" \
    -d "{\"type\":\"TOTAL_LOCKDOWN\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >/dev/null || true
fi
echo "Sistema en modo LOCKDOWN."
