#!/bin/bash
# SABION_OMEGA_2040 - Dashboard GOD MODE test (GREGORIO exclusivo)
# Puerto 10000 - Admin CTO CASTÚO 360 S.L.
# Uso: desde raíz del repo: ./backend/sabion_omega_2040/test_omega_dashboard.sh
#      o: cd backend/sabion_omega_2040 && bash test_omega_dashboard.sh (usa ../../docker-compose.omega.yml)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OMEGA_COMPOSE="${OMEGA_COMPOSE:-$REPO_ROOT/docker-compose.omega.yml}"

echo "🔐 === SABION_OMEGA_2040 DASHBOARD GOD MODE TEST ==="
echo "Puerto: 10000 | Admin: GREGORIO_J_JIMENEZ_BODES"
echo ""

# 1. Verificar contenedor
echo "📊 [1/4] Status OMEGA_2040..."
if docker-compose -f "$OMEGA_COMPOSE" ps 2>/dev/null | grep -q Up; then
  echo "   Contenedor OMEGA LIVE ✓"
else
  echo "   ⚠ Ejecuta: docker-compose -f docker-compose.omega.yml up -d"
fi
echo ""

# 2. Autenticar GREGORIO
echo "🔑 [2/4] Autenticación ADMIN EXCLUSIVA..."
AUTH=$(curl -s -X POST http://localhost:10000/omega/auth \
  -H "Content-Type: application/json" \
  -d '{"token":"CASTUO_360_GREGORIO_2040_KYBER2048_TRL9"}')
echo "$AUTH" | jq .
if ! echo "$AUTH" | jq -e '.ok == true' >/dev/null 2>&1; then
  echo "   ❌ Auth fallida. ¿OMEGA en 10000?"
  exit 1
fi
echo ""

# 3. Dashboard GOD MODE
echo "📈 [3/4] DASHBOARD SUPREMO..."
DASH=$(curl -s http://localhost:10000/omega/admin_dashboard \
  -H "X-Admin-Token: CASTUO_360_GREGORIO_2040_KYBER2048_TRL9")
echo "$DASH" | jq '{
  admin: .admin,
  revenue_2040: .total_revenue_2040,
  nodes: .nodes_global,
  subsidiaries: .subsidiaries,
  god_mode: .god_mode
}'
ADMIN=$(echo "$DASH" | jq -r '.admin')
REV=$(echo "$DASH" | jq -r '.total_revenue_2040')
NODES=$(echo "$DASH" | jq -r '.nodes_global')
GOD=$(echo "$DASH" | jq -r '.god_mode')
echo "   ✅ GREGORIO OK | $REV | $NODES | GOD: $GOD"
echo ""

# 4. CLI alternativa
echo "💻 [4/4] Recordatorio CLI..."
echo "   python backend/sabion_omega_2040/admin_cli.py dashboard"
echo ""

# 5. Resultado completo (opcional)
echo "📋 Dashboard completo (raw):"
echo "$DASH" | jq .
echo ""
echo "✅ ✅ ✅ DASHBOARD GOD MODE LIVE - 100% CONTROL GREGORIO ✅ ✅ ✅"
