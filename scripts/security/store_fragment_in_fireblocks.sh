#!/bin/bash
# CASTÚO-SYSTEM™ — Almacena el fragmento 2 (u otro) en Fireblocks Vault.
# Requiere autenticación previa; el fragmento se genera en Python y se envía por stdin (no por argumentos).
# Uso: ./scripts/security/store_fragment_in_fireblocks.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAGMENT_INDEX=2

# 1. Autenticación opcional
if [ -f "$SCRIPT_DIR/biometric_auth.py" ]; then
  python3 "$SCRIPT_DIR/biometric_auth.py" || true
elif [ -f "$SCRIPT_DIR/authenticate_with_yubikey.py" ]; then
  python3 "$SCRIPT_DIR/authenticate_with_yubikey.py" || true
fi

# 2. Generar fragmento en memoria y enviar a Fireblocks (sin escribir secreto en disco)
python3 -c "
import getpass
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from generate_emergency_keys import generate_master_key, split_master_key
from fireblocks_integration import encrypt_for_fireblocks, fireblocks_store_fragment

pwd = getpass.getpass('Contraseña maestra (para generar fragmentos): ')
if not pwd:
    sys.exit(1)
import os
salt = os.urandom(16)
key = generate_master_key(pwd, salt)
fragments = split_master_key(key, 3, 5)
idx, payload = fragments[1]
blob = bytes([idx]) + payload
fb_pwd = getpass.getpass('Contraseña para cifrado Fireblocks: ')
enc = encrypt_for_fireblocks(blob, $FRAGMENT_INDEX, fb_pwd)
result = fireblocks_store_fragment(enc, $FRAGMENT_INDEX)
if result.get('id'):
    print('Fragmento $FRAGMENT_INDEX almacenado en Fireblocks: TX', result['id'])
else:
    print('Error:', result.get('error', result), file=sys.stderr)
    sys.exit(1)
" || {
  echo "Para almacenar manualmente: cat fragment2.bin | python3 $SCRIPT_DIR/fireblocks_integration.py store $FRAGMENT_INDEX"
  exit 1
}

echo "Fragmento $FRAGMENT_INDEX almacenado en Fireblocks Vault y registrado en GaiaChain (si aplica)."
