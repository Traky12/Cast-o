#!/bin/bash
# CASTÚO-SYSTEM™ v10.1 — Sustitución de placeholders legales post-registro (15/03/2026)
# Uso: RPI_NUMBER=RPI-1234/2026 EUIPO_NUMBER=EUIPO-5678/2026 ./replace-placeholders.sh
# Ejecutar desde raíz del repo (17:00 CET tras registro RPI + EUIPO).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

RPI_NUMBER="${RPI_NUMBER:-RPI-XXXX/2026}"
EUIPO_NUMBER="${EUIPO_NUMBER:-EUIPO-YYYY/2026}"

if [ "$RPI_NUMBER" = "RPI-XXXX/2026" ] || [ "$EUIPO_NUMBER" = "EUIPO-YYYY/2026" ]; then
  echo "⚠️  Defina RPI_NUMBER y EUIPO_NUMBER con los números reales."
  echo "   Ejemplo: RPI_NUMBER=RPI-1234/2026 EUIPO_NUMBER=EUIPO-5678/2026 $0"
  exit 1
fi

echo "Sustituyendo placeholders en docs/legal..."
for f in docs/legal/*.md docs/legal/*.txt docs/legal/v1.0.0/*.md 2>/dev/null; do
  [ -f "$f" ] || continue
  sed -i.bak "s|RPI-XXXX/2026|$RPI_NUMBER|g" "$f"
  sed -i.bak "s|EUIPO-YYYY/2026|$EUIPO_NUMBER|g" "$f"
  sed -i.bak "s|XXXX/2026|$RPI_NUMBER|g" "$f"
  sed -i.bak "s|YYYY/2026|$EUIPO_NUMBER|g" "$f"
  rm -f "${f}.bak"
  echo "  ✓ $f"
done

echo "✅ Placeholders sustituidos. Siguiente: git add docs/legal && git commit -m 'LEGAL: RPI + EUIPO registrados [TRL9]' && git tag -a v1.0.0 -m 'Versión legal certificada'"
