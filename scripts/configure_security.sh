#!/bin/bash
# Configuración de parámetros de seguridad avanzada CASTÚO-SYSTEM™
# Uso: ./scripts/configure_security.sh [--dry-run]
set -euo pipefail

DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true && echo "Modo simulación (--dry-run)"

run() { $DRY_RUN && echo "Simulación: $*" || "$@"; }

echo "1/10 PodSecurityPolicy..."
run kubectl apply -f kubernetes/security-policies.yaml
run kubectl label ns castuo-prod pod-security.kubernetes.io/enforce=restricted --overwrite 2>/dev/null || true

echo "2/10 NetworkPolicies..."
run kubectl apply -f kubernetes/network-policies.yaml

echo "3/10 ConfigMaps de seguridad..."
run kubectl apply -f kubernetes/security-configmap.yaml
run kubectl apply -f kubernetes/prod-configmap.yaml 2>/dev/null || true

echo "4/10 Alertas Prometheus..."
run kubectl apply -f monitoring/prometheus/prod-alert-rules.yaml 2>/dev/null || true
run kubectl apply -f monitoring/prometheus/prod-security-alert-rules.yaml 2>/dev/null || true

echo "5/10 HPA..."
run kubectl apply -f kubernetes/prod-hpa.yaml 2>/dev/null || true

echo "6/10 CronJobs de seguridad..."
run kubectl apply -f kubernetes/forensic-audit-cronjob.yaml 2>/dev/null || true
run kubectl apply -f kubernetes/prod-key-rotation-cronjob.yaml 2>/dev/null || true

echo "7/10 Parámetros en coordinador FL..."
if ! $DRY_RUN; then
  kubectl set env deployment/secure-federated-coordinator -n castuo-prod \
    DEFENSE_ENABLED=true \
    FORENSIC_ENABLED=true \
    DEFENSE_POLICY=default \
    LEGAL_COMPLIANCE_MODE=strict 2>/dev/null || true
  kubectl rollout restart deployment/secure-federated-coordinator -n castuo-prod 2>/dev/null || true
fi

echo "8/10 Parámetros en sistema de defensa..."
if ! $DRY_RUN; then
  kubectl set env deployment/defense-system -n castuo-prod \
    ALERT_THRESHOLD_NETWORK=0.001 \
    ALERT_THRESHOLD_BEHAVIOR=0.0005 \
    MAX_EVIDENCE_RETENTION=90 \
    LEGAL_COMPLIANCE_MODE=strict \
    DEFENSE_POLICY=default \
    RESPONSE_TIME_TARGET=100 \
    FALSE_POSITIVE_TARGET=0.001 2>/dev/null || true
  kubectl rollout restart deployment/defense-system -n castuo-prod 2>/dev/null || true
fi

echo "9/10 Verificación..."
if ! $DRY_RUN; then
  kubectl get configmap security-config -n castuo-prod -o yaml 2>/dev/null | grep -E "ENCRYPTION_ALGORITHM|DEFENSE_POLICY|LEGAL_COMPLIANCE" || true
  kubectl get networkpolicy -n castuo-prod 2>/dev/null || true
  kubectl get prometheusrules -n castuo-prod 2>/dev/null || true
fi

echo "10/10 Resumen..."
if $DRY_RUN; then
  echo "Simulación completada. Para aplicar: ./scripts/configure_security.sh"
else
  echo "Configuración de seguridad aplicada."
  echo "Verificar: kubectl describe configmap security-config -n castuo-prod"
fi
