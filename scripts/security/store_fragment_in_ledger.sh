#!/bin/bash
# CASTÚO-SYSTEM™ — Genera fragmentos Shamir y almacena el fragmento 2 en Ledger Vault.
# No expone el fragmento por línea de comandos; lo pasa por stdin al script Python.
# Uso: ./scripts/security/store_fragment_in_ledger.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASTUO_ROOT="${CASTUO_ROOT:-/opt/castuo}"
FRAGMENTS_DIR="${CASTUO_FRAGMENTS_DIR:-/opt/castuo/secure_fragments}"
FRAGMENT_INDEX=2

# 1. Generar fragmentos si no existen (o usar los ya generados)
if [ ! -f "$FRAGMENTS_DIR/ledger_vault_fragment.enc" ] && [ -f "$SCRIPT_DIR/generate_emergency_keys.py" ]; then
  echo "Genera primero los fragmentos con: python3 $SCRIPT_DIR/generate_emergency_keys.py"
  echo "Luego copia el fragmento 2 (33 bytes: index + 32 bytes) a un archivo y pásalo por stdin, o usa el archivo local."
  echo "Ejemplo: cat fragment2.enc | python3 $SCRIPT_DIR/ledger_vault_integration.py store $FRAGMENT_INDEX"
  exit 1
fi

# 2. Si existe fragmento local ledger (formato: salt+iv+ct), extraer payload descifrado requiere contraseña.
# Alternativa: generar en memoria y enviar por stdin (solo Python puede hacerlo sin escribir disco).
echo "Para almacenar el fragmento 2 en Ledger Vault:"
echo "  1. Ejecuta generate_emergency_keys.py y anota el directorio de salida."
echo "  2. Usa reconstruct_master_key para obtener la llave (no recomendado exponer)."
echo "  Forma recomendada: ejecutar el flujo integrado desde Python."
echo ""
echo "Flujo integrado (Python):"
python3 -c "
import getpass
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from generate_emergency_keys import generate_master_key, split_master_key, store_fragment
from ledger_vault_integration import store_fragment_in_ledger

pwd = getpass.getpass('Contraseña maestra (para generar fragmentos): ')
if not pwd:
    sys.exit(1)
salt = __import__('os').urandom(16)
key = generate_master_key(pwd, salt)
fragments = split_master_key(key, 3, 5)
# Fragmento 2 = index 1 (0-based)
idx, payload = fragments[1]
# Payload para Ledger: 33 bytes (index + 32 bytes)
blob = bytes([idx]) + payload
ledger_pwd = getpass.getpass('Contraseña para cifrado Ledger Vault: ')
result = store_fragment_in_ledger(2, blob, ledger_pwd)
if result.get('id'):
    print('Fragmento 2 almacenado en Ledger Vault:', result['id'])
else:
    print('Error:', result.get('error', result), file=sys.stderr)
    sys.exit(1)
" 2>/dev/null || {
  echo "Ejecutando almacenamiento directo (fragmento por stdin)..."
  echo "Si tienes el archivo del fragmento 2 (33 bytes), ejecuta:"
  echo "  cat fragment2.bin | python3 $SCRIPT_DIR/ledger_vault_integration.py store 2"
  exit 0
}
