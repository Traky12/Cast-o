#!/bin/bash
# CASTÚO-SYSTEM™ | Upgrade TRL10 → TRL11: baseline v1.1.0, merge v1.2.0, sign, deploy, verify
# Uso: ./scripts/deploy/trl11-upgrade.sh
# Requiere: verify-integrity.sh, sign-all.sh en docker/castuo-bookstack; acceso a repo y Docker

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

BOOKSTACK_DIR="$REPO_ROOT/docker/castuo-bookstack"
VERIFY_URL="${CASTUO_VERIFY_URL:-https://89.167.5.233:8080}"

echo "=== TRL11 Upgrade: baseline v1.1.0 ==="
git fetch --tags 2>/dev/null || true
if git rev-parse v1.1.0 >/dev/null 2>&1; then
  git checkout v1.1.0
else
  echo "⚠️ Tag v1.1.0 no existe. Usando rama actual como baseline."
fi

if [ -d "$BOOKSTACK_DIR" ] && [ -f "$BOOKSTACK_DIR/verify-integrity.sh" ]; then
  cd "$BOOKSTACK_DIR"
  ./verify-integrity.sh || { echo "❌ Integridad fallida en baseline."; exit 1; }
  cd "$REPO_ROOT"
fi

echo "=== Merge TRL11 (v1.2.0) ==="
if git rev-parse v1.2.0 >/dev/null 2>&1; then
  git merge v1.2.0 --no-ff -m "chore: TRL11 merge v1.2.0"
else
  echo "⚠️ Tag v1.2.0 no existe. Omitiendo merge."
fi

if [ -d "$BOOKSTACK_DIR" ] && [ -f "$BOOKSTACK_DIR/sign-all.sh" ]; then
  cd "$BOOKSTACK_DIR"
  ./sign-all.sh
  cd "$REPO_ROOT"
fi

if [ -f "$BOOKSTACK_DIR/verify-integrity.sh" ]; then
  cd "$BOOKSTACK_DIR"
  ./verify-integrity.sh || { echo "❌ Verificación post-merge fallida."; exit 1; }
  cd "$REPO_ROOT"
fi

echo "=== Docker Compose (pull + up) ==="
if [ -f "$BOOKSTACK_DIR/docker-compose.yml" ]; then
  cd "$BOOKSTACK_DIR"
  docker compose pull 2>/dev/null || docker-compose pull 2>/dev/null || true
  docker compose up -d 2>/dev/null || docker-compose up -d 2>/dev/null || true
  cd "$REPO_ROOT"
fi

echo "=== Verificación TRL11 LIVE ==="
if command -v curl >/dev/null 2>&1; then
  if curl -sf --connect-timeout 5 "$VERIFY_URL" >/dev/null 2>&1; then
    echo "✅ TRL11 UPGRADE COMPLETE — $VERIFY_URL respondiendo"
  else
    echo "⚠️ No se pudo verificar $VERIFY_URL (curl fallido o no configurado)"
  fi
else
  echo "⚠️ curl no disponible para verificación final"
fi

echo "✅ TRL11 upgrade script finalizado."
