#!/bin/bash
# CASTÚO-SYSTEM™ — Generación de checksums para documentos legales (anti-hacking v1.0)
# Ejecutar desde repo root. Opcional: firmar legal.checksums con HSM.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CHECKSUMS_FILE="$SCRIPT_DIR/legal.checksums"
: > "$CHECKSUMS_FILE"

for f in docs/legal/*.md docs/legal/*.txt docs/legal/v1.0.0/*.md 2>/dev/null; do
  [ -f "$f" ] || continue
  sha256sum "$f" >> "$CHECKSUMS_FILE"
done

echo "Checksums generados en $CHECKSUMS_FILE"
if [ -n "$HSM_KEY_PATH" ] && [ -f "$HSM_KEY_PATH" ]; then
  openssl dgst -sha256 -sign "$HSM_KEY_PATH" -out "$CHECKSUMS_FILE.sig" "$CHECKSUMS_FILE"
  echo "Firma guardada en $CHECKSUMS_FILE.sig"
fi
