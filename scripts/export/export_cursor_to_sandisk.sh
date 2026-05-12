#!/bin/bash
# CASTÚO-SYSTEM™ — Exporta binarios/configs de Cursor al SanDisk seguro (firmas HSM).
# Montar antes con mount-sandisk. Uso: ./scripts/export/export_cursor_to_sandisk.sh

set -e
DEST="${CASTUO_SANDISK_ROOT:-/mnt/sandisk/CASTUO_SECURE}/cursor"
mkdir -p "$DEST"/{bin,config,logs}
[ -d /opt/cursor ] && cp -a /opt/cursor/bin/* "$DEST/bin/" 2>/dev/null || true
[ -d /opt/cursor/config ] && cp -a /opt/cursor/config/* "$DEST/config/" 2>/dev/null || true
# Firmar índice si existe verify-with-hsm
VERIFY_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/cursor/verify-with-hsm.py"
if [ -f "$VERIFY_SCRIPT" ]; then
  for f in "$DEST/bin"/*; do
    [ -f "$f" ] && python3 "$VERIFY_SCRIPT" "$f" 2>/dev/null || true
  done
fi
echo "Cursor exportado a $DEST"
