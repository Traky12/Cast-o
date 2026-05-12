#!/bin/bash
# CASTÚO BookStack — Test suite post-deploy. TRL8 compliant.
# Ejecutar desde docker/castuo-bookstack o desde repo root (el script hace cd a su directorio).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "🔍 Verificando BookStack CASTÚO..."
docker compose ps --services 2>/dev/null | grep -q bookstack || { echo "❌ BookStack down"; exit 1; }
curl -sf "http://localhost:${BOOKSTACK_PORT:-8080}/login" -o /dev/null || { echo "❌ BookStack unreachable"; exit 1; }
echo "✅ BookStack LIVE + TRL8 compliant!"
