# Runbook de Operaciones de Seguridad — Sistema de Defensa

## 1. Procedimientos de emergencia

### 1.1. Ataque DDoS detectado

**Síntomas**

- Alertas `HighFLLatency` en Grafana
- Tráfico de red anómalo en Prometheus
- Múltiples evidencias de tipo `network_anomaly`

**Acciones**

1. Verificar evidencias:
   ```bash
   kubectl exec -n castuo-prod deploy/defense-system -- \
     python -c "
   from backend.security.forensic_analyzer import ForensicAnalyzer
   from backend.security.end_to_end_encryption import EndToEndEncryption
   from backend.compliance.immutable_traceability import ImmutableTraceability
   e=EndToEndEncryption(); t=ImmutableTraceability(e); fa=ForensicAnalyzer(e,t)
   r=fa.get_evidence_report()
   print('Evidencias recientes:', r['metadata']['total_evidences'])
   "
   ```

2. Aumentar capacidad:
   ```bash
   kubectl scale deployment/secure-federated-coordinator -n castuo-prod --replicas=10
   kubectl scale deployment/defense-system -n castuo-prod --replicas=5
   ```

3. Activar modo defensivo:
   ```bash
   kubectl set env deployment/defense-system -n castuo-prod DEFENSE_MODE=aggressive
   ```

4. Generar informe forense:
   ```bash
   kubectl exec -n castuo-prod deploy/defense-system -- \
     python -m backend.compliance.forensic_audit --period 1 --output /var/traceability/ddos_report.json
   ```

### 1.2. Comportamiento malicioso detectado

**Síntomas**

- Alertas `behavior_anomaly`
- Patrones de acceso sospechosos
- Múltiples intentos de login fallidos

**Acciones**

1. Revisar evidencias:
   ```bash
   kubectl exec -n castuo-prod deploy/defense-system -- \
     python -m backend.compliance.forensic_audit --period 1 --output /var/traceability/behavior_audit.json
   ```

2. Rotar claves de cifrado:
   ```bash
   kubectl create job -n castuo-prod --from=cronjob/he-key-rotation manual-key-rotation-$(date +%s)
   ```

3. Notificación a afectados según GDPR Art. 34 (procedimiento interno).

---

## 2. Mantenimiento

### 2.1. Actualización de modelos de defensa

Frecuencia: semanal.

```bash
kubectl exec -n castuo-prod deploy/defense-system -- \
  python -c "
from backend.ai.federated_defense import FederatedDefenseSystem
# Entrenar con datos recientes (integrar con script específico)
"
kubectl rollout restart deployment/defense-system -n castuo-prod
```

### 2.2. Backup de evidencias forenses

```bash
kubectl exec -n castuo-prod deploy/defense-system -- \
  python -c "
from backend.security.forensic_analyzer import ForensicAnalyzer
from backend.security.end_to_end_encryption import EndToEndEncryption
from backend.compliance.immutable_traceability import ImmutableTraceability
e=EndToEndEncryption(); t=ImmutableTraceability(e); fa=ForensicAnalyzer(e,t)
import json
r=fa.get_evidence_report()
with open('/var/traceability/backup_evidences.json','w') as f: json.dump(r,f,indent=2)
"
kubectl cp castuo-prod/$(kubectl get pods -n castuo-prod -l app=defense-system -o jsonpath='{.items[0].metadata.name}'):/var/traceability/backup_evidences.json ./backups/
```

---

## 3. Contactos de emergencia

| Tipo de incidente        | Responsable   | Contacto                   | Escalado      |
|--------------------------|---------------|----------------------------|---------------|
| Ataque DDoS              | Seguridad     | security@castuo-system.eu | CISO → CEO    |
| Brecha de datos          | Privacidad    | privacy@castuo-system.eu  | Legal → Consejo |
| Fallo sistema de defensa  | DevOps        | devops@castuo-system.eu   | CTO → CEO     |
| Incidente cumplimiento   | Legal         | legal@castuo-system.eu    | Consejo       |
| Amenaza infraestructura  | Infraestructura | infra@castuo-system.eu  | CIO → CEO     |

---

## 4. Métricas clave

| Métrica                      | Umbral crítico | Verificación                          |
|-----------------------------|----------------|----------------------------------------|
| Tasa anomalías de red       | >0.01          | Prometheus / alertas                   |
| Tasa anomalías comportamiento | >0.005      | Prometheus / alertas                   |
| Tiempo respuesta defensa    | >100 ms        | Logs / métricas                        |
| CPU pods defensa            | >80 %          | `kubectl top pod -n castuo-prod -l app=defense-system` |
| Memoria pods defensa        | >1.5 Gi        | `kubectl top pod -n castuo-prod -l app=defense-system` |

---

## 5. Escalado y sensibilidad

```bash
# Más réplicas
kubectl scale deployment/defense-system -n castuo-prod --replicas=10

# Mayor sensibilidad
kubectl set env deployment/defense-system -n castuo-prod \
  ALERT_THRESHOLD_NETWORK=0.005 ALERT_THRESHOLD_BEHAVIOR=0.002

# Modo agresivo
kubectl set env deployment/defense-system -n castuo-prod DEFENSE_MODE=aggressive
```

---

## 6. Informes legales

```bash
# Informe para autoridades
kubectl exec -n castuo-prod deploy/defense-system -- python -c "
from backend.compliance.gaiachain_integration import GaiaChainForensicRegistry
import os, json
gc = GaiaChainForensicRegistry(os.getenv('GAIA_CHAIN_URL'), os.getenv('GAIA_CHAIN_API_KEY'))
r = gc.generate_legal_report('INC-2023-11-15', {'start':'2023-11-01T00:00:00Z','end':'2023-11-15T23:59:59Z'})
with open('/var/traceability/legal_report.json','w') as f: json.dump(r,f,indent=2)
"
kubectl cp castuo-prod/$(kubectl get pods -n castuo-prod -l app=defense-system -o jsonpath='{.items[0].metadata.name}'):/var/traceability/legal_report.json ./legal_reports/
```

---

## 7. Contención de brechas

1. Aislar: `kubectl scale deployment/secure-federated-coordinator -n castuo-prod --replicas=0` y `defense-system --replicas=0`.
2. Generar informe forense completo (period 7, severity critical).
3. Notificar autoridades según GDPR Art. 33.
4. Rotar todas las claves (CronJob manual + nuevos secrets).
5. Restaurar desde backup limpio.
6. Reanudar con réplicas reducidas y monitoreo intensivo.
