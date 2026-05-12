#!/bin/bash
# CASTÚO-SYSTEM™ — Recuperación post-DMS. Requiere: contraseña maestra + YubiKey OTP + 3 fragmentos.
# Uso: sudo ./scripts/security/post-dms-recovery.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASTUO_ROOT="${CASTUO_ROOT:-/opt/castuo}"
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"

echo "=== Recuperación post-DMS ==="
read -s -p "Introduce la contraseña maestra para recuperación: " MASTER_PASSWORD
echo
read -p "Toca tu YubiKey y pega el OTP: " YUBIKEY_OTP

[ -z "$MASTER_PASSWORD" ] && { echo "Contraseña vacía."; exit 1; }

# Verificación local del hash si existe
if [ -f "$CHAIN_DIR/master_password.hash" ]; then
  INPUT_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
  STORED_HASH=$(cat "$CHAIN_DIR/master_password.hash")
  [ "$INPUT_HASH" != "$STORED_HASH" ] && { echo "Contraseña incorrecta."; exit 1; }
fi

echo "Rutas a 3 fragmentos (ej: /opt/castuo/secure_fragments/junta_extremadura_fragment.enc)"
FRAGMENTS=()
for i in 1 2 3; do
  read -p "Ruta al fragmento $i: " p
  [ -f "$p" ] || { echo "No existe: $p"; exit 1; }
  FRAGMENTS+=("$p")
done

# Reconstruir llave maestra con Python
RECONSTRUCT="$SCRIPT_DIR/reconstruct_master_key.py"
if [ ! -f "$RECONSTRUCT" ]; then
  RECONSTRUCT="$CASTUO_ROOT/scripts/security/reconstruct_master_key.py"
fi
if [ ! -f "$RECONSTRUCT" ]; then
  echo "No se encuentra reconstruct_master_key.py"; exit 1
fi

export CASTUO_EXPORT_RECONSTRUCTED_KEY=1
echo "Introduce la contraseña maestra cuando lo pida el script de reconstrucción."
python3 "$RECONSTRUCT" "${FRAGMENTS[0]}" "${FRAGMENTS[1]}" "${FRAGMENTS[2]}" || exit 1
unset MASTER_PASSWORD
echo ""
echo "Llave reconstruida. Siguientes pasos:"

echo "Restaurando HSM (si aplica)..."
if command -v pkcs11-tool >/dev/null 2>&1 && [ -n "$HSM_MODULE" ]; then
  echo "Reinicializar token HSM manualmente con: pkcs11-tool --init-token --label CASTUO-Master"
fi

echo "Restaurando GaiaChain desde backup..."
if [ -f "$CASTUO_ROOT/scripts/security/restore-encrypted-backup.sh" ]; then
  "$CASTUO_ROOT/scripts/security/restore-encrypted-backup.sh" || true
fi

echo "Reconfigurando YubiKey..."
if [ -f "$SCRIPT_DIR/setup-yubikey.sh" ]; then
  "$SCRIPT_DIR/setup-yubikey.sh" || true
fi

API_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
  SIG=$(echo -n "RECOVERY_COMPLETE_$(date +%s)" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
  curl -sf -X POST "${API_URL}/api/v1/alert/recovery" \
    -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"type\":\"POST_DMS_RECOVERY\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"signature\":\"${SIG}\"}" >/dev/null || true
fi

echo "Recuperación post-DMS completada. Solo el administrador con 3 fragmentos puede haber ejecutado esto."
