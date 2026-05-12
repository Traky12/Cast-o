#!/bin/bash
# CASTÚO-SYSTEM™ — Activa el protocolo DMS (Dead Man's Switch). Delega en secure-destruction-protocol.sh.
# Requiere autenticación previa (authenticate.py o YubiKey + contraseña).
# Uso: sudo ./scripts/security/activate-dms.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$SCRIPT_DIR/secure-destruction-protocol.sh" ]; then
  exec "$SCRIPT_DIR/secure-destruction-protocol.sh"
fi
echo "secure-destruction-protocol.sh no encontrado."
exit 1
