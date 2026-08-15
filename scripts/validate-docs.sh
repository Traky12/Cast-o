#!/usr/bin/env bash
set -euo pipefail

required=(
  docs/QUICK-REFERENCE.md
  docs/CASTUO-SYSTEM-ANALISIS-COMPLETO.md
  docs/RESUMEN-EJECUTIVO-1PAGE.md
  docs/RELEASE-NOTES.md
)

for file in "${required[@]}"; do
  test -s "$file"
  grep -q '^# ' "$file"
done

# Umbrales mínimos específicos de esta plantilla. No se confunde la presencia
# de documentación con evidencia operativa, que se valida en otros gates.
test "$(wc -l < docs/QUICK-REFERENCE.md)" -ge 20
test "$(wc -l < docs/CASTUO-SYSTEM-ANALISIS-COMPLETO.md)" -ge 80
test "$(wc -l < docs/RESUMEN-EJECUTIVO-1PAGE.md)" -ge 20
test "$(wc -l < docs/RELEASE-NOTES.md)" -ge 5

echo "Documentation validation OK"
