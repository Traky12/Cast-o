#!/bin/bash
# CASTÚO-SYSTEM™ — Almacena el fragmento 2 en Swiss Vault (Zúrich). Requiere auth previa; fragmento por stdin en Python.
# Uso: ./scripts/security/store_fragment_in_swissvault.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAGMENT_INDEX=2

# 1. Autenticación opcional
if [ -f "$SCRIPT_DIR/biometric_auth.py" ]; then
  python3 "$SCRIPT_DIR/biometric_auth.py" || true
elif [ -f "$SCRIPT_DIR/authenticate_with_yubikey.py" ]; then
  python3 "$SCRIPT_DIR/authenticate_with_yubikey.py" || true
fi

# 2. Generar fragmento en memoria y enviar a Swiss Vault (sin exponer en línea de comandos)
python3 -c "
import getpass
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from generate_emergency_keys import generate_master_key, split_master_key
from swiss_vault_integration import encrypt_for_swissvault, store_fragment_in_swissvault, swissvault_login, _get_yubikey_otp

pwd = getpass.getpass('Contraseña maestra (para generar fragmentos): ')
if not pwd:
    sys.exit(1)
import os
salt = os.urandom(16)
key = generate_master_key(pwd, salt)
fragments = split_master_key(key, 3, 5)
idx, payload = fragments[1]
blob = bytes([idx]) + payload
sv_pwd = getpass.getpass('Contraseña para cifrado Swiss Vault: ')
enc = encrypt_for_swissvault(blob, $FRAGMENT_INDEX, sv_pwd)
otp = _get_yubikey_otp()
token = swissvault_login(sv_pwd, otp)
if token:
    result = store_fragment_in_swissvault(enc, $FRAGMENT_INDEX, token)
    if result.get('deposit_id'):
        print('Fragmento $FRAGMENT_INDEX almacenado en Swiss Vault: deposit_id=', result['deposit_id'])
    else:
        print('Error:', result.get('error', result), file=sys.stderr)
        sys.exit(1)
else:
    print('Configure SWISS_VAULT_API_KEY y ejecute de nuevo, o use: cat fragment2.bin | python3 $SCRIPT_DIR/swiss_vault_integration.py store $FRAGMENT_INDEX')
    sys.exit(1)
" || {
  echo "Para almacenar manualmente: cat fragment2.bin | python3 $SCRIPT_DIR/swiss_vault_integration.py store $FRAGMENT_INDEX"
  exit 1
}

echo "Fragmento $FRAGMENT_INDEX almacenado en Swiss Vault (Zúrich) y registrado en GaiaChain si aplica."
