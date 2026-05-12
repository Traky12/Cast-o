#!/usr/bin/env bash
set -euo pipefail

test -f docs/QUICK-REFERENCE.md
test -f docs/CASTUO-SYSTEM-ANALISIS-COMPLETO.md
test -f docs/RESUMEN-EJECUTIVO-1PAGE.md
test -f docs/RELEASE-NOTES.md

test "$(wc -l < docs/QUICK-REFERENCE.md)" -ge 100
test "$(wc -l < docs/CASTUO-SYSTEM-ANALISIS-COMPLETO.md)" -ge 900
test "$(wc -l < docs/RESUMEN-EJECUTIVO-1PAGE.md)" -ge 200
test "$(wc -l < docs/RELEASE-NOTES.md)" -ge 5

grep -q '^# ' docs/QUICK-REFERENCE.md
grep -q '^# ' docs/CASTUO-SYSTEM-ANALISIS-COMPLETO.md
grep -q '^# ' docs/RESUMEN-EJECUTIVO-1PAGE.md
grep -q '^# ' docs/RELEASE-NOTES.md

echo "Documentation validation OK"
