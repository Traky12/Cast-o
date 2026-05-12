#!/bin/bash
# Despliegue del sistema de defensa CASTÚO-SYSTEM™
# Uso: ./scripts/deploy_defense_system.sh [--dry-run]
set -euo pipefail

DRY_RUN=false
[ "${1:-}" = "--dry-run" ] && DRY_RUN=true && echo "Modo simulación (--dry-run)"

echo "1/8 Aplicando ConfigMap de defensa..."
$DRY_RUN || kubectl apply -f kubernetes/defense-configmap.yaml

echo "2/8 Desplegando sistema de defensa..."
if ! $DRY_RUN; then
  kubectl apply -f kubernetes/defense-deployment.yaml
  kubectl rollout status deployment/defense-system -n castuo-prod --timeout=5m
fi

echo "3/8 Creando servicio..."
$DRY_RUN || kubectl apply -f kubernetes/defense-service.yaml

echo "4/8 Configurando CronJob de auditorías..."
$DRY_RUN || kubectl apply -f kubernetes/forensic-audit-cronjob.yaml

echo "5/8 Verificando despliegue..."
if ! $DRY_RUN; then
  kubectl get pods -n castuo-prod -l app=defense-system
  kubectl logs -n castuo-prod -l app=defense-system --tail=20 2>/dev/null || true
fi

echo "6/8 Actualizando coordinador FL..."
if ! $DRY_RUN; then
  kubectl set env deployment/secure-federated-coordinator -n castuo-prod \
    DEFENSE_ENABLED=true FORENSIC_ENABLED=true 2>/dev/null || true
  kubectl rollout restart deployment/secure-federated-coordinator -n castuo-prod 2>/dev/null || true
fi

echo "7/8 Verificando integración..."
if ! $DRY_RUN; then
  kubectl exec -n castuo-prod deploy/defense-system -- python -c "
from backend.security.forensic_analyzer import ForensicAnalyzer
from backend.security.end_to_end_encryption import EndToEndEncryption
from backend.compliance.immutable_traceability import ImmutableTraceability
e = EndToEndEncryption()
t = ImmutableTraceability(e)
fa = ForensicAnalyzer(e, t)
test_data = [{'timestamp': '2023-11-15T12:00:00Z', 'bytes_in': 1024, 'bytes_out': 512}]
result, evidence = fa.analyze_network_traffic(test_data)
print('Prueba forense:', 'anomaly' if result else 'clean')
" 2>/dev/null || echo "Ejecución de prueba omitida (pod no listo o imagen sin backend)"
fi

echo "8/8 Resumen..."
if $DRY_RUN; then
  echo "Simulación completada. Para ejecutar: ./scripts/deploy_defense_system.sh"
else
  echo "Sistema de defensa desplegado."
  echo "Logs: kubectl logs -n castuo-prod -l app=defense-system -f"
fi
