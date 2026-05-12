#!/bin/bash
# Auditoría sencilla de seguridad para CASTÚO-SYSTEM
set -euo pipefail

echo "🔍 Auditoría de seguridad CASTÚO-SYSTEM"
echo "======================================="

echo "📋 Contenedores activos:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
echo

echo "🛡️ Comprobando health de API (si está expuesta en 8000):"
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  curl -s http://localhost:8000/health | head -c 200 && echo
else
  echo "No se pudo acceder a http://localhost:8000/health (puerto cerrado o auth requerida)."
fi
echo

echo "📜 Últimas líneas de logs de seguridad (si existen):"
if [ -f backend/security/security.log ]; then
  tail -n 20 backend/security/security.log
else
  echo "No se encontró backend/security/security.log"
fi
echo

echo "💾 Volúmenes Docker relacionados con backups:"
docker volume ls | grep -i backup || echo "Sin volúmenes con 'backup' en el nombre."
echo

echo "✅ Auditoría básica completada."

