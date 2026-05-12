#!/bin/bash
# CASTÚO-SYSTEM™ — Recuperación de emergencia por servicio (anti-hacking v1.0)
# Uso: ./emergency-recovery.sh <sabionda-core|gaiachain|cursor> <revision|version|tag>

set -e
SERVICE="${1:?Servicio requerido: sabionda-core|gaiachain|cursor}"
LAST_KNOWN_GOOD="${2:?Revisión/versión/tag conocido bueno}"

recover_sabionda() {
  echo "Recuperando Sabionda Core a revisión $LAST_KNOWN_GOOD..."
  if command -v kubectl >/dev/null 2>&1; then
    kubectl rollout undo deployment/sabionda-core --to-revision="$LAST_KNOWN_GOOD" || true
  fi
  if command -v curl >/dev/null 2>&1; then
    if curl -sf http://sabionda-core:8000/health 2>/dev/null | grep -q "ok\|healthy"; then
      echo "Sabionda Core recuperado."
      return 0
    fi
  fi
  return 1
}

recover_gaiachain() {
  echo "Recuperando GaiaChain a bloque/snapshot $LAST_KNOWN_GOOD..."
  if [ -n "$SNAPSHOT_URL" ]; then
    wget -q -O /tmp/snapshot.tar.gz "$SNAPSHOT_URL" || true
    tar -xzf /tmp/snapshot.tar.gz -C "${GAIACHAIN_DATA_DIR:-/var/lib/gaiachain}" 2>/dev/null || true
    rm -f /tmp/snapshot.tar.gz
  fi
  echo "Restart gaiachain manual si aplica: systemctl restart gaiachain"
  return 0
}

recover_cursor() {
  echo "Recuperando Cursor a versión $LAST_KNOWN_GOOD..."
  if command -v kubectl >/dev/null 2>&1; then
    kubectl set image deployment/cursor cursor=ghcr.io/castuo-system/cursor:"$LAST_KNOWN_GOOD" 2>/dev/null || true
  fi
  echo "Cursor image actualizada."
  return 0
}

case "$SERVICE" in
  sabionda-core) recover_sabionda ;;
  gaiachain)     recover_gaiachain ;;
  cursor)        recover_cursor ;;
  *)
    echo "Servicio no reconocido: $SERVICE"
    exit 1
    ;;
esac

# Registrar en GaiaChain si hay API key
if [ -n "$GAIA_CHAIN_API_KEY" ]; then
  curl -s -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/recovery" \
    -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"EMERGENCY_RECOVERY\",\"service\":\"$SERVICE\",\"version\":\"$LAST_KNOWN_GOOD\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" || true
fi
echo "Recuperación registrada (si GAIA_CHAIN_API_KEY definido)."
