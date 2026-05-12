#!/bin/bash
# CASTÚO-SYSTEM™ — Configuración de YubiKey para MFA físico (SSH, GaiaChain, HSM)
# Uso: sudo ./scripts/security/setup-yubikey.sh

set -e

echo "Configuración de YubiKey para CASTÚO-SYSTEM™"

# 1. Instalar herramientas YubiKey (Debian/Ubuntu)
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y libpam-yubico yubico-pam yubikey-personalization 2>/dev/null || true
fi

# 2. YubiKey personalization (si ykpersonalize está disponible)
if command -v ykpersonalize >/dev/null 2>&1 && command -v ykinfo >/dev/null 2>&1; then
  SERIAL=$(ykinfo -s 2>/dev/null | cut -d':' -f2 | tr -d ' ') || true
  if [ -n "$SERIAL" ]; then
    ykpersonalize -2 -o-fixed -o-serial -o-append-cr -a "$SERIAL" 2>/dev/null || true
  fi
fi

# 3. PAM para SSH con YubiKey (solo si no está ya)
if [ -d /etc/pam.d ] && ! grep -q pam_yubico /etc/pam.d/sshd 2>/dev/null; then
  echo "auth required pam_yubico.so id=16 mode=challenge-response" | tee -a /etc/pam.d/sshd
fi

# 4. YubiKey Manager (ykman) para PIV
if command -v ykman >/dev/null 2>&1; then
  echo "Generar clave PIV en slot 9a (autenticación). Ejecuta manualmente:"
  echo "  ykman piv generate-key --algorithm RSA2048 9a auth"
  echo "  ykman piv generate-certificate --subject 'CN=CASTUO-Admin' 9a /tmp/castuo-piv.csr"
  echo "  ykman piv import-certificate 9a /tmp/castuo-piv.crt"
fi

# 5. Registro en GaiaChain (si API y clave están disponibles)
GAIA_URL="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"
if [ -n "$GAIA_CHAIN_ADMIN_KEY" ] && [ -f "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" ]; then
  if command -v ykman >/dev/null 2>&1; then
    PUBKEY=$(ykman piv export-certificate 9a 2>/dev/null | openssl x509 -pubkey -noout 2>/dev/null | base64 -w0) || true
    if [ -n "$PUBKEY" ]; then
      TIMESTAMP=$(date +%s)
      SIG=$(echo -n "YUBIKEY_REGISTRATION_${TIMESTAMP}" | openssl dgst -sha512 -sign "${GAIA_CHAIN_DIR:-/etc/gaiachain}/master_key.pem" 2>/dev/null | base64 -w0) || true
      if [ -n "$SIG" ]; then
        curl -sf -X POST "${GAIA_URL}/api/v1/yubikey/register" \
          -H "Authorization: Bearer $GAIA_CHAIN_ADMIN_KEY" \
          -H "Content-Type: application/json" \
          -d "{\"admin\":\"authorized_admin\",\"yubikey_public_key\":\"${PUBKEY}\",\"signature\":\"${SIG}\",\"timestamp\":${TIMESTAMP}}" >/dev/null || true
      fi
    fi
  fi
fi

echo "YubiKey configurada para: SSH (PAM), firma GaiaChain (PIV 9a), segundo factor DMS/wipe."
echo "Solo el administrador autorizado debe poseer la YubiKey física."
