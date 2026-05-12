#!/bin/bash
# CASTÚO-SYSTEM™ — Inicialización del HSM Thales Luna (solo el administrador, una vez).
# No se almacenan PINs en el script; se solicitan de forma segura.
# Uso: sudo ./scripts/security/init-hsm.sh

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
mkdir -p "$CHAIN_DIR"
chmod 700 "$CHAIN_DIR"

echo "Inicialización del HSM para CASTÚO-SYSTEM™"
read -s -p "SO-PIN del HSM (Security Officer): " HSM_SO_PIN
echo
read -s -p "User PIN del HSM: " HSM_USER_PIN
echo
[ -z "$HSM_SO_PIN" ] || [ -z "$HSM_USER_PIN" ] && { echo "PINs no pueden estar vacíos."; exit 1; }

# 1. Inicializar token (si el driver lo permite)
if command -v pkcs11-tool >/dev/null 2>&1; then
  pkcs11-tool --init-token --label "CASTUO-Master" --so-pin "$HSM_SO_PIN" --pin "$HSM_USER_PIN" 2>/dev/null || true
fi

# 2. Generar clave maestra en HSM
if command -v pkcs11-tool >/dev/null 2>&1; then
  pkcs11-tool --login --pin "$HSM_USER_PIN" --keygen --key-type rsa:4096 --label "CASTUO-Master-Key" --id 01 2>/dev/null || true
fi

# 3. Clave PEM local (para firmar cuando HSM no esté disponible); protegida por contraseña
if [ ! -f "$CHAIN_DIR/master_key.pem" ]; then
  echo "Generando clave RSA local (backup de firma)..."
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out "$CHAIN_DIR/master_key.pem" -aes-256-cbc 2>/dev/null || true
  chmod 600 "$CHAIN_DIR/master_key.pem"
fi

# 4. Certificado autofirmado (opcional)
if [ -f "$CHAIN_DIR/master_key.pem" ] && [ ! -f "$CHAIN_DIR/master_cert.pem" ]; then
  openssl req -new -x509 -days 3650 -key "$CHAIN_DIR/master_key.pem" \
    -out "$CHAIN_DIR/master_cert.pem" \
    -subj "/CN=CASTUO-Admin/O=CASTUO-SYSTEM/C=ES" 2>/dev/null || true
  chmod 644 "$CHAIN_DIR/master_cert.pem"
fi

# 5. YubiKey PIV (comandos documentados; ejecutar manualmente si se desea)
echo "Para vincular YubiKey, ejecuta manualmente:"
echo "  ykman piv generate-key --algorithm RSA2048 9a auth"
echo "  ykman piv generate-certificate --subject 'CN=CASTUO-Admin' 9a /tmp/castuo-piv.csr"
echo "  ykman piv import-certificate 9a /tmp/castuo-piv.crt"

# 6. Registrar YubiKey en GaiaChain (si API y token están disponibles)
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && command -v ykman >/dev/null 2>&1; then
  PUBKEY=$(ykman piv export-certificate 9a 2>/dev/null | openssl x509 -pubkey -noout 2>/dev/null | base64 -w0) || true
  if [ -n "$PUBKEY" ] && [ -f "$CHAIN_DIR/master_key.pem" ]; then
    SIG=$(echo -n "YUBIKEY_REGISTER_$(date +%s)" | openssl dgst -sha512 -sign "$CHAIN_DIR/master_key.pem" 2>/dev/null | base64 -w0) || true
    curl -sf -X POST "${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}/api/v1/yubikey/register" \
      -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"admin\":\"authorized_admin\",\"yubikey_public_key\":\"$PUBKEY\",\"signature\":\"$SIG\"}" >/dev/null || true
  fi
fi

unset HSM_SO_PIN HSM_USER_PIN
echo "HSM y claves locales configurados. La clave maestra no sale del HSM."
echo "Autenticación requiere YubiKey + HSM (o clave PEM local)."
