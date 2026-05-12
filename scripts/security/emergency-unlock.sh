#!/bin/bash
# CASTÚO-SYSTEM™ — Desbloqueo tras emergencia (solo administrador autorizado)

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
API_BASE="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"
[ ! -f "$CHAIN_DIR/master_password.hash" ] && { echo "No hay hash de contraseña maestra."; exit 1; }

read -s -p "Introduce la contraseña maestra para desbloquear: " MASTER_PASSWORD
echo
INPUT_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
STORED_HASH=$(cat "$CHAIN_DIR/master_password.hash")
unset MASTER_PASSWORD
[ "$INPUT_HASH" != "$STORED_HASH" ] && { echo "Contraseña incorrecta."; exit 1; }

if [ -n "$GAIA_CHAIN_ADMIN_KEY" ]; then
  LAST=$(curl -sf "$API_BASE/api/v1/emergency/latest" -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" | jq -r '.type // empty')
  [ "$LAST" != "TOTAL_LOCKDOWN" ] && echo "No hay bloqueo activo registrado."
fi

ufw --force reset 2>/dev/null || true
ufw default deny incoming 2>/dev/null || true
ufw default allow outgoing 2>/dev/null || true
ufw allow 8000/tcp 2>/dev/null || true
ufw allow 8080/tcp 2>/dev/null || true
ufw allow 22/tcp 2>/dev/null || true
ufw --force enable 2>/dev/null || true

systemctl start gaiachain 2>/dev/null || true
systemctl start suricata 2>/dev/null || true
systemctl start wazuh-agent 2>/dev/null || true
curl -sf -X POST "$API_BASE/api/v1/emergency/resolve" -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" -H "Content-Type: application/json" -d "{\"type\":\"TOTAL_UNLOCK\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >/dev/null || true
echo "Sistema desbloqueado."
