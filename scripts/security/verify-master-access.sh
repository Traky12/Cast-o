#!/bin/bash
# CASTÚO-SYSTEM™ — Verificación de acceso con contraseña maestra
# Si la contraseña coincide con el hash almacenado, exporta GAIA_CHAIN_ADMIN_KEY para la sesión.

set -e
CHAIN_DIR="${GAIA_CHAIN_DIR:-/etc/gaiachain}"
[ ! -f "$CHAIN_DIR/master_password.hash" ] && { echo "No hay hash registrado. Ejecuta register-master-password.sh primero."; exit 1; }

read -s -p "Introduce la contraseña maestra: " MASTER_PASSWORD
echo
INPUT_HASH=$(echo -n "$MASTER_PASSWORD" | openssl dgst -sha512 -binary | xxd -p -c 256)
STORED_HASH=$(cat "$CHAIN_DIR/master_password.hash")

if [ "$INPUT_HASH" != "$STORED_HASH" ]; then
  unset MASTER_PASSWORD INPUT_HASH
  echo "Acceso denegado."
  exit 1
fi

# Exportar clave derivada para esta sesión (opcional)
if [ -f "$CHAIN_DIR/master_key.hex" ]; then
  export GAIA_CHAIN_ADMIN_KEY=$(cat "$CHAIN_DIR/master_key.hex")
fi
unset MASTER_PASSWORD INPUT_HASH STORED_HASH
echo "Acceso concedido. GAIA_CHAIN_ADMIN_KEY exportada para esta sesión si existía master_key.hex."
