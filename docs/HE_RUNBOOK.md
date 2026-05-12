# Runbook de operaciones para Federated Learning con HE

## 1. Procedimientos estándar

### 1.1. Rotación de claves HE

- **Frecuencia**: Cada 90 días.
- **Responsable**: Equipo de seguridad.

```bash
# 1. Staging
KUBE_NAMESPACE=castuo-staging python backend/scripts/rotate_he_keys.py --scheme CKKS

# 2. Producción (sin simulación)
python backend/scripts/rotate_he_keys.py --scheme CKKS --no-dry-run

# 3. Verificar jobs (Kubernetes)
kubectl get jobs -n castuo | findstr he-key-rotation
```

### 1.2. Monitoreo de rendimiento

- **Frecuencia**: Diaria.
- **Herramientas**: Prometheus + Grafana.

```bash
# Uso de memoria de los pods del coordinador
kubectl top pod -n castuo -l app=he-federated-coordinator
```

## 2. Procedimientos de emergencia

### 2.1. Fallo en cifrado HE

**Síntomas**: `TensealException` en logs, timeouts en agregación.

**Acciones**:

```bash
# 1. Deshabilitar HE temporalmente
kubectl set env deploy/he-federated-coordinator -n castuo USE_HE=false

# 2. Notificar a seguridad (canal definido internamente)

# 3. Revisar logs
kubectl logs -n castuo -l app=he-federated-coordinator --tail=100

# 4. Rehabilitar cuando esté resuelto
kubectl set env deploy/he-federated-coordinator -n castuo USE_HE=true
```

### 2.2. Detección de outliers masivos

**Síntomas**: Alertas HE_OutlierRate &gt; 0,5 %, logs con “outliers detectados”.

**Acciones**:

```bash
# 1. Aislar nodos afectados (etiquetar para cuarentena)
kubectl label pods -n castuo -l app=he-federated-coordinator status=quarantined --overwrite

# 2. Analizar (si existe script)
kubectl exec -n castuo deploy/he-federated-coordinator -- \
  python -m backend.scripts.analyze_outliers --severity high

# 3. Registrar incidente en GaiaChain (vía traceability o script de registro)
python backend/scripts/register_he_incident.py --type outlier_detection --severity high
```

## 3. Métricas clave

| Métrica              | Umbral crítico | Verificación                          |
|----------------------|----------------|----------------------------------------|
| Tasa de errores HE   | &gt;0,1 %      | HPA / alertas Prometheus               |
| Uso memoria por pod  | &gt;1,5 Gi     | `kubectl top pod -n castuo`            |
| Tiempo de agregación | &gt;100 ms     | Benchmark / métricas del coordinador   |
| Outliers por hora    | &gt;5          | Consulta Prometheus / GaiaChain        |

## 4. Contactos de soporte

| Equipo       | Responsable   | Canal              | Horario |
|--------------|---------------|--------------------|---------|
| Seguridad    | (definir)     | #security-alerts   | 24/7    |
| DevOps       | (definir)     | #devops-oncall     | 24/7    |
| Cumplimiento | (definir)     | compliance@...     | L–V 9–18 |
| Soporte N1   | (definir)     | +34 900 123 456    | 24/7    |

## 5. Referencias

- Guía de migración: `docs/HE_MIGRATION_GUIDE.md`
- Políticas FL/HE: `docs/compliance/POLICIES_v2.1.md` (sección 3)
- Scripts: `backend/scripts/migrate_to_he_federated_learning.py`, `rotate_he_keys.py`, `generate_he_compliance_report.py`
