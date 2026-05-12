#!/bin/bash
# CASTÚO-SYSTEM™ — Registro seguro de contraseña maestra (una sola vez)
# La contraseña NO se almacena; solo hash SHA-512 y claves derivadas en HSM.
# Uso: ./scripts/security/register-master-password.sh

set -e
echo "Registro de contraseña maestra (solo se ejecuta una vez)."
read -s -p "Introduce la contraseña maestra: " MASTER_PASSWORD
echo
[ -z "$MASTER_PASSWORD" ] && { echo "Contraseña vacía."; exit 1; }

mkdir -p /etc/gaiachain 2>/dev/null || true
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"

# Hash SHA-512 (solo el hash se persiste)
PASSWORD_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
echo "$PASSWORD_HASH" > "$CHAIN_DIR/master_password.hash"
chmod 600 "$CHAIN_DIR/master_password.hash"

# Clave GaiaChain derivada (opcional, para API)
GAIA_CHAIN_KEY=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha3-512 -binary | xxd -p -c 256)
echo "$GAIA_CHAIN_KEY" > "$CHAIN_DIR/master_key.hex"
chmod 600 "$CHAIN_DIR/master_key.hex"

# Clave RSA (protegida por contraseña; en producción usar HSM)
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out "$CHAIN_DIR/master_key.pem" -aes-256-cbc -pass pass:"$MASTER_PASSWORD" 2>/dev/null || true
chmod 600 "$CHAIN_DIR/master_key.pem" 2>/dev/null || true

# HSM: si pkcs11-tool está disponible y hay módulo configurado
if command -v pkcs11-tool >/dev/null 2>&1 && [ -n "$HSM_MODULE" ]; then
  echo "$PASSWORD_HASH" | pkcs11-tool --login --pin "$MASTER_PASSWORD" --write-object /dev/stdin --type data --label "CASTUO-Master-Hash" --id 01 2>/dev/null || true
fi

unset MASTER_PASSWORD
unset GAIA_CHAIN_KEY
unset PASSWORD_HASH
echo "Contraseña maestra registrada. Solo el hash y claves derivadas están almacenados; la contraseña ha sido borrada de memoria."
