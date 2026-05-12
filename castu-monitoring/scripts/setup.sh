#!/bin/bash
# CASTUO-SYSTEM™ | Despliega Prometheus + Grafana + git-exporter + Alertmanager
# Ejecutar desde la raíz del repo: ./castu-monitoring/scripts/setup.sh
# O desde castu-monitoring: ./scripts/setup.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$MONITORING_DIR"

echo "📂 Directorio: $MONITORING_DIR"
docker-compose up -d

echo "⏳ Esperando 30s a que Prometheus y Grafana estén listos..."
sleep 30

# Datasource Prometheus en Grafana (puerto 3001)
curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "basicAuth": false
  }' \
  http://admin:castuo123@localhost:3001/api/datasources 2>/dev/null || true

# Importar dashboard
DASH_PATH="$MONITORING_DIR/grafana/dashboards/castu-git.json"
if [ -f "$DASH_PATH" ]; then
  DASHBOARD_JSON=$(cat "$DASH_PATH" | jq -c '.')
  curl -s -X POST -H "Content-Type: application/json" \
    -d "{\"dashboard\": $DASHBOARD_JSON, \"overwrite\": true}" \
    http://admin:castuo123@localhost:3001/api/dashboards/db 2>/dev/null || true
fi

echo ""
echo "✅ CASTUO-SYSTEM™ Monitoring desplegado:"
echo "   - Grafana:    http://localhost:3001 (admin / castuo123)"
echo "   - Prometheus: http://localhost:9090"
echo "   - git-exporter: http://localhost:9091/metrics"
echo "   - Alertmanager: http://localhost:9093"
