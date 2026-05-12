#!/bin/bash
# CASTÚO-SYSTEM™ — Recuperación de emergencia con 3/5 fragmentos. Delega en post-dms-recovery.sh.
# Uso: sudo ./scripts/security/emergency-recovery.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$SCRIPT_DIR/post-dms-recovery.sh" ]; then
  exec "$SCRIPT_DIR/post-dms-recovery.sh"
fi
# Alternativa: reconstrucción manual con fragmentos
echo "post-dms-recovery.sh no encontrado. Para recuperar:"
echo "  1. python3 $SCRIPT_DIR/reconstruct_master_key.py fragment1.enc fragment2.enc fragment3.enc"
echo "  2. python3 $SCRIPT_DIR/retrieve_bank_fragments.py  # si usas bóvedas bancarias"
echo "  3. scripts/security/restore-encrypted-backup.sh"
exit 1
