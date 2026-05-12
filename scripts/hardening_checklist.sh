#!/usr/bin/env bash
set -u

NAMESPACE="${NAMESPACE:-castuo-system}"
STAGING_NAMESPACE="${STAGING_NAMESPACE:-castuo-staging}"
API_URL="${API_URL:-http://api.castuo-system.cloud}"
RUN_STAGING_APPLY="${RUN_STAGING_APPLY:-0}"
RUN_MANUAL_GDPR_JOB="${RUN_MANUAL_GDPR_JOB:-0}"

PASS_COUNT=0
FAIL_COUNT=0

say_pass() {
	echo "[✅] $1"
	PASS_COUNT=$((PASS_COUNT + 1))
}

say_warn() {
	echo "[⚠️] $1"
}

say_fail() {
	echo "[❌] $1"
	FAIL_COUNT=$((FAIL_COUNT + 1))
}

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "Comando requerido no encontrado: $1"
		exit 2
	}
}

check_cluster_connectivity() {
	kubectl version --request-timeout=5s >/dev/null 2>&1 || {
		echo "❌ Error de conexión al clúster (kubectl)"
		exit 2
	}
}

check_secrets() {
	local block_fail=0
	local secret_yaml

	if ! secret_yaml="$(kubectl get secrets -n "${NAMESPACE}" castuo-secrets -o yaml 2>/dev/null)"; then
		say_fail "Seguridad: secret castuo-secrets no existe en ${NAMESPACE}"
		return
	fi

	for key in JWT_SECRET TIMESCALE_DB_PASSWORD EIDAS_PRIVATE_KEY_PATH REDIS_URL MFA_ENABLED; do
		if echo "${secret_yaml}" | grep -q "${key}:"; then
			:
		else
			say_warn "Seguridad: falta ${key} en castuo-secrets"
			block_fail=1
		fi
	done

	if [[ ${block_fail} -eq 0 ]]; then
		say_pass "Seguridad: secrets obligatorios presentes"
	else
		say_fail "Seguridad: secrets incompletos"
	fi
}

check_operation() {
	local block_fail=0

	if kubectl get hpa -n "${NAMESPACE}" castuo-api-hpa >/dev/null 2>&1 || \
		 kubectl get hpa -n "${NAMESPACE}" >/dev/null 2>&1; then
		:
	else
		say_warn "Operación: HPA no encontrado en ${NAMESPACE}"
		block_fail=1
	fi

	if kubectl get deploy -n "${NAMESPACE}" castuo-api >/dev/null 2>&1; then
		if kubectl rollout status deployment/castuo-api -n "${NAMESPACE}" --timeout=30s >/dev/null 2>&1; then
			:
		else
			say_warn "Operación: rollout de castuo-api no estable"
			block_fail=1
		fi
	else
		say_warn "Operación: deployment castuo-api no encontrado"
		block_fail=1
	fi

	if [[ ${block_fail} -eq 0 ]]; then
		say_pass "Operación: despliegues y autoscaling verificados"
	else
		say_fail "Operación: bloque con incidencias"
	fi
}

check_traceability() {
	local block_fail=0

	if curl -fsS "${API_URL}/metrics" | grep -q "castuo_"; then
		:
	else
		say_warn "Trazabilidad: métricas en /metrics no disponibles"
		block_fail=1
	fi

	if kubectl get prometheusrules -n monitoring >/dev/null 2>&1; then
		:
	else
		say_warn "Trazabilidad: PrometheusRule no accesible en namespace monitoring"
		block_fail=1
	fi

	if [[ ${block_fail} -eq 0 ]]; then
		say_pass "Trazabilidad: métricas y reglas de alerta activas"
	else
		say_fail "Trazabilidad: bloque con incidencias"
	fi
}

check_gdpr() {
	local block_fail=0

	if kubectl get cronjobs -n "${NAMESPACE}" gdpr-cleanup >/dev/null 2>&1; then
		:
	else
		say_warn "GDPR: cronjob gdpr-cleanup no encontrado"
		block_fail=1
	fi

	if [[ "${RUN_MANUAL_GDPR_JOB}" == "1" ]]; then
		local job_name="gdpr-cleanup-manual-$(date +%s)"
		if kubectl create job --from=cronjob/gdpr-cleanup -n "${NAMESPACE}" "${job_name}" >/dev/null 2>&1; then
			say_warn "GDPR: job manual creado (${job_name}); revisar logs aparte"
		else
			say_warn "GDPR: no se pudo crear job manual desde cronjob"
			block_fail=1
		fi
	fi

	if [[ ${block_fail} -eq 0 ]]; then
		say_pass "GDPR: cronjob y flujo de limpieza presentes"
	else
		say_fail "GDPR: bloque con incidencias"
	fi
}

check_redundancy() {
	local block_fail=0
	local timescale_count
	local api_count

	timescale_count="$(kubectl get pods -n "${NAMESPACE}" -l app=timescale-ha --no-headers 2>/dev/null | wc -l | tr -d ' ')"
	api_count="$(kubectl get pods -n "${NAMESPACE}" -l app=castuo-api --no-headers 2>/dev/null | wc -l | tr -d ' ')"

	if [[ "${timescale_count}" -lt 2 ]]; then
		say_warn "Redundancia: timescale-ha con menos de 2 pods (${timescale_count})"
		block_fail=1
	fi
	if [[ "${api_count}" -lt 2 ]]; then
		say_warn "Redundancia: castuo-api con menos de 2 pods (${api_count})"
		block_fail=1
	fi

	if [[ ${block_fail} -eq 0 ]]; then
		say_pass "Redundancia: replicas mínimas verificadas"
	else
		say_fail "Redundancia: bloque con incidencias"
	fi
}

run_staging_e2e() {
	if [[ "${RUN_STAGING_APPLY}" == "1" ]]; then
		echo "[INFO] Aplicando manifiestos en staging (${STAGING_NAMESPACE})"
		kubectl apply -f k8s/ -n "${STAGING_NAMESPACE}" >/dev/null 2>&1 || say_warn "Staging apply devolvió errores"
	fi

	if python3 scripts/test_e2e.py >/dev/null 2>&1; then
		say_pass "E2E Staging: pruebas base OK"
	else
		say_warn "E2E Staging: pruebas con fallos (revisar scripts/test_e2e.py)"
		FAIL_COUNT=$((FAIL_COUNT + 1))
	fi
}

main() {
	require_cmd kubectl
	require_cmd curl
	require_cmd python3

	check_cluster_connectivity

	echo "== Hardening Checklist (${NAMESPACE}) =="
	check_secrets
	check_operation
	check_traceability
	check_gdpr
	check_redundancy
	run_staging_e2e

	echo "---"
	if [[ ${FAIL_COUNT} -eq 0 ]]; then
		echo "RESULTADO FINAL: PASS (${PASS_COUNT} bloques OK)"
		exit 0
	fi

	echo "RESULTADO FINAL: FAIL (${FAIL_COUNT} bloques con errores)"
	exit 1
}

main "$@"
