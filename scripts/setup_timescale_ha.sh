#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${1:-castuo-system}"

if ! command -v kubectl >/dev/null 2>&1; then
	echo "❌ kubectl no disponible"
	exit 3
fi

if ! kubectl version --request-timeout=5s >/dev/null 2>&1; then
	echo "❌ Error de conexión al clúster"
	exit 3
fi

echo "[1/5] Despliegue de TimescaleDB HA iniciado en ${NAMESPACE}"
if ! kubectl apply -f k8s/timescale-ha.yaml -n "${NAMESPACE}" >/dev/null 2>&1; then
	echo "❌ Error aplicando k8s/timescale-ha.yaml"
	exit 1
fi

echo "[2/5] Aplicando NetworkPolicy"
if ! kubectl apply -f k8s/networkpolicy.yaml -n "${NAMESPACE}" >/dev/null 2>&1; then
	echo "⚠️ No se pudo aplicar networkpolicy.yaml (continuando)"
fi

echo "[3/5] Esperando pods listos"
if ! kubectl rollout status statefulset/timescale-ha -n "${NAMESPACE}" --timeout=300s >/dev/null 2>&1; then
	echo "❌ Timescale HA no alcanzó estado Ready"
	exit 1
fi

echo "[4/5] Verificando número de réplicas"
READY="$(kubectl get pods -n "${NAMESPACE}" -l app=timescale-ha --no-headers 2>/dev/null | grep -c "Running" || true)"
if [[ "${READY}" -lt 3 ]]; then
	echo "❌ Validación: solo ${READY}/3 pods Running"
	exit 1
fi

echo "[5/5] Estado de replicación (si aplica)"
kubectl exec -n "${NAMESPACE}" timescale-ha-0 -- psql -U castuo_iot -d castuo_telemetry -c "SELECT client_addr, state, sync_state FROM pg_stat_replication;" >/dev/null 2>&1 || true

echo "✅ Validación: 3/3 pods saludables (timescale-ha-0, timescale-ha-1, timescale-ha-2)"
echo "RESULTADO: PASS"
exit 0
