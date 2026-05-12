#!/bin/bash
# Rollback a bases de datos en memoria en caso de fallo en PostgreSQL.
# Uso: desde la raíz del repo: chmod +x scripts/rollback_to_memory.sh && ./scripts/rollback_to_memory.sh
# Requiere: Docker y docker-compose.ctaex.yml (el backend seguirá usando los mismos compose pero sin depender de PostgreSQL si se desactiva DB_HOST).

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker/docker-compose.ctaex.yml}"

echo "🛑 Deteniendo servicios..."
docker compose -f "$COMPOSE_FILE" down || true

echo "🔄 Revirtiendo cambios en backend (opcional: solo si se modificó para usar PostgreSQL)..."
# Revertir backend/database.py y routers que apunten a PostgreSQL (si se usó rama o parche)
if git diff --name-only HEAD -- backend/database.py backend/routers/pro_accounts.py 2>/dev/null | grep -q .; then
  git checkout -- backend/database.py backend/routers/pro_accounts.py 2>/dev/null || true
fi

echo "📝 Para usar solo memoria, asegúrate de que DB_HOST no esté definido en .env (o usa USE_POSTGRES=false si el backend lo soporta)."
echo "🚀 Iniciando servicios (con docker-compose.ctaex.yml; postgres seguirá levantado pero el backend puede usar memoria si no tiene DB_HOST)..."
docker compose -f "$COMPOSE_FILE" up -d --build backend 2>/dev/null || docker compose -f "$COMPOSE_FILE" up -d

echo "✅ Verificando estado..."
docker compose -f "$COMPOSE_FILE" ps 2>/dev/null || docker ps
sleep 3
BACKEND_CONTAINER=$(docker compose -f "$COMPOSE_FILE" ps -q backend 2>/dev/null || true)
if [ -n "$BACKEND_CONTAINER" ]; then
  echo "--- Últimas líneas del backend ---"
  docker logs "$BACKEND_CONTAINER" --tail 20 2>/dev/null || true
fi

echo "✨ Rollback completado. Si el backend está configurado sin DB_HOST, usará bases de datos en memoria."
echo "   Documentación: docs/POSTGRESQL-MIGRATION-PLAN.md (Sección 11. Plan de contingencia)."
