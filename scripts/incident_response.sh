#!/bin/bash
# Respuesta a incidentes de seguridad
# Uso: ./scripts/incident_response.sh [critical|high|medium|low] [descripción]
set -euo pipefail

SEVERITY=${1:-medium}
DESCRIPTION=${2:-"Incidente de seguridad genérico"}
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
INCIDENT_ID="INC-$(date +%Y%m%d)-$(openssl rand -hex 4 2>/dev/null || echo "0000")"
EVIDENCE_DIR="/var/traceability/incidents/${INCIDENT_ID}"

echo "Registrando incidente $INCIDENT_ID ($SEVERITY): $DESCRIPTION"

# 1. Registrar en trazabilidad (desde pod de defensa si existe)
kubectl exec -n castuo-prod deploy/defense-system -- env INCIDENT_ID="$INCIDENT_ID" SEVERITY="$SEVERITY" DESCRIPTION="$DESCRIPTION" TIMESTAMP="$TIMESTAMP" python -c "
import os
from backend.compliance.immutable_traceability import ImmutableTraceability
from backend.security.end_to_end_encryption import EndToEndEncryption
e = EndToEndEncryption()
t = ImmutableTraceability(e)
t.register_event({
    'type': 'security_incident_initiated',
    'incident_id': os.environ.get('INCIDENT_ID', ''),
    'severity': os.environ.get('SEVERITY', ''),
    'description': os.environ.get('DESCRIPTION', ''),
    'timestamp': os.environ.get('TIMESTAMP', ''),
    'normative_references': ['ISO_27001:A.16.1.1', 'GDPR:Art.33', 'NIST_SP_800-61']
})
print('OK')
" 2>/dev/null || echo "No se pudo registrar en pod (namespace o deploy no disponible)"

# 2. Acciones por severidad
case $SEVERITY in
  critical)
    echo "Severidad crítica: aplicando medidas de emergencia..."
    kubectl scale deployment/secure-federated-coordinator -n castuo-prod --replicas=0 2>/dev/null || true
    kubectl scale deployment/defense-system -n castuo-prod --replicas=2 2>/dev/null || true
    kubectl create job -n castuo-prod --from=cronjob/he-key-rotation "emergency-key-rotation-$INCIDENT_ID" 2>/dev/null || true
    ;;
  high)
    echo "Severidad alta: modo defensivo..."
    kubectl set env deployment/defense-system -n castuo-prod DEFENSE_MODE=aggressive 2>/dev/null || true
    kubectl set env deployment/defense-system -n castuo-prod ALERT_THRESHOLD_NETWORK=0.0005 2>/dev/null || true
    ;;
  medium|low)
    echo "Severidad $SEVERITY: monitoreando."
    ;;
esac

# 3. Informe forense preliminar
kubectl exec -n castuo-prod deploy/defense-system -- \
  python -m backend.compliance.forensic_audit --period 1 --output "/var/traceability/incident_${INCIDENT_ID}_report.json" 2>/dev/null || true

# 4. Registrar acciones
TS2=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
kubectl exec -n castuo-prod deploy/defense-system -- env INCIDENT_ID="$INCIDENT_ID" SEVERITY="$SEVERITY" TS2="$TS2" python -c "
import os
from backend.compliance.immutable_traceability import ImmutableTraceability
from backend.security.end_to_end_encryption import EndToEndEncryption
e = EndToEndEncryption()
t = ImmutableTraceability(e)
t.register_event({
    'type': 'security_incident_actions_taken',
    'incident_id': os.environ.get('INCIDENT_ID', ''),
    'severity': os.environ.get('SEVERITY', ''),
    'actions': ['Incident registered', 'Severity-based measures applied', 'Preliminary report requested'],
    'timestamp': os.environ.get('TS2', ''),
    'normative_references': ['ISO_27001:A.16.1.4', 'GDPR:Art.33', 'NIST_SP_800-61:6.3']
})
print('OK')
" 2>/dev/null || true

echo ""
echo "Incidente $INCIDENT_ID registrado."
echo "Próximos pasos: revisar evidencias en /var/traceability/incident_${INCIDENT_ID}_report.json (dentro del pod); si critical/high coordinar con legal y programar revisión post-incidente."
echo "ID para escalado: $INCIDENT_ID"
