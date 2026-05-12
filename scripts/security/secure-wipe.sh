#!/bin/bash
# CASTÚO-SYSTEM™ — Borrado seguro de discos (DoD 5220.22-M). Delega en secure-wipe-disks.sh.
# Uso: sudo ./scripts/security/secure-wipe.sh [opcional: target para compatibilidad]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$SCRIPT_DIR/secure-wipe-disks.sh" ]; then
  exec "$SCRIPT_DIR/secure-wipe-disks.sh"
fi
echo "secure-wipe-disks.sh no encontrado."
exit 1
