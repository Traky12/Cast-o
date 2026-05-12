#!/bin/bash
# Despliegue CASTUO Drones (backend + MQTT). Ejecutar desde raíz del repo.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "=== CASTUO-SYSTEM™ Drones ==="
echo "Construyendo backend..."
docker compose -f castu_drones/docker-compose.yml build fastapi 2>/dev/null || true
echo "Levantando servicios..."
docker compose -f castu_drones/docker-compose.yml up -d
echo ""
echo "Servicios:"
echo "  - FastAPI (drones/riego/chatbot): http://localhost:8000"
echo "  - MQTT: mqtt://localhost:1883"
echo "  - Odoo: usar docker-compose.odoo-erp-legal.yml por separado"
echo ""
echo "Telemetría de prueba:"
echo '  curl -X POST http://localhost:8000/drones/1/telemetry -H "Content-Type: application/json" -d "{\"lat\":39.47,\"lon\":-0.38,\"alt\":10,\"battery\":95}"'
