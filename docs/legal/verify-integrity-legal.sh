#!/bin/bash
# CASTÚO-SYSTEM™ v10.1 + anti-hacking v1.0 — Verificación de integridad de documentos legales (TRL9)
# 1) Opcional: falla si quedan placeholders RPI/EUIPO (SKIP_PLACEHOLDER_CHECK=1 para omitir).
# 2) Checksums SHA256 de documentos críticos.
# Ejecutar desde repo root: docs/legal/verify-integrity-legal.sh
# Generar checksums: docs/legal/generate-checksums.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Placeholders: fallar si aún hay XXXX/2026 o YYYY/2026 (post-registro debe estar sustituido)
if [ "${SKIP_PLACEHOLDER_CHECK}" != "1" ]; then
  if grep -r "XXXX/2026\|YYYY/2026" docs/legal/ --include="*.md" --include="*.txt" 2>/dev/null | grep -q .; then
    echo "❌ ERROR: Placeholders RPI/EUIPO no sustituidos en docs/legal/"
    grep -r "XXXX/2026\|YYYY/2026" docs/legal/ --include="*.md" --include="*.txt" 2>/dev/null || true
    exit 1
  fi
fi

CHECKSUMS_FILE="$SCRIPT_DIR/legal.checksums"
if [ ! -f "$CHECKSUMS_FILE" ]; then
  echo "⚠️  No existe $CHECKSUMS_FILE. Generando checksums actuales..."
  (cd "$REPO_ROOT" && sha256sum docs/legal/CASTUO-Legal-Framework.md docs/legal/TRL9-AntiTampering-Certification.md docs/legal/TRL9-status.txt docs/legal/v1.0.0/README.md 2>/dev/null) > "$CHECKSUMS_FILE"
  echo "   Creado. Revise y vuelva a ejecutar para verificar."
  exit 0
fi

echo "🔍 Verificando integridad de documentos legales..."
if ! sha256sum -c "$CHECKSUMS_FILE" --quiet 2>/dev/null; then
  echo "❌ ERROR: Uno o más documentos legales han sido modificados (TRL9)."
  sha256sum -c "$CHECKSUMS_FILE" 2>/dev/null || true
  exit 1
fi
echo "✅ Todos los documentos legales son íntegros (TRL9)."
