#!/bin/sh
# CASTUO-SYSTEM™ — Instala los hooks de Git desde scripts/git-hooks/ a .git/hooks/
# Ejecutar desde la raíz del repo: ./scripts/setup-git-hooks.sh

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GIT_DIR="$ROOT/.git"
HOOKS_SRC="$ROOT/scripts/git-hooks"

if [ ! -d "$GIT_DIR" ]; then
  echo "❌ No se encuentra .git. Ejecuta este script desde la raíz del repositorio."
  exit 1
fi

if [ ! -d "$HOOKS_SRC" ]; then
  echo "❌ No se encuentra scripts/git-hooks/."
  exit 1
fi

for hook in "$HOOKS_SRC"/*; do
  [ -f "$hook" ] || continue
  name="$(basename "$hook")"
  dest="$GIT_DIR/hooks/$name"
  cp "$hook" "$dest"
  chmod +x "$dest"
  echo "✅ Instalado: .git/hooks/$name"
done

echo ""
echo "CASTUO-SYSTEM™ — Git hooks instalados. Ver docs/GIT-CURSOR.md para uso y trazabilidad TX."
