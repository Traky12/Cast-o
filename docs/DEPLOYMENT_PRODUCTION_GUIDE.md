# Guía completa para despliegue final en producción — CASTÚO-SYSTEM™ v2.1

## 1. Preparación del entorno de producción

### 1.1. Requisitos previos

| Componente     | Versión mínima | Verificación                          |
|----------------|----------------|----------------------------------------|
| Kubernetes     | 1.25+          | `kubectl version`                       |
| Helm           | 3.10+          | `helm version`                         |
| Docker         | 20.10+         | `docker --version`                     |
| Python         | 3.11+          | `python --version`                     |
| TenSEAL        | 0.3.0          | `pip show tenseal`                     |
| cert-manager   | 1.8+           | `kubectl get pods -n cert-manager`     |
| Prometheus     | 2.30+          | `kubectl get pods -n monitoring`       |
| GaiaChain Node | 2.1+           | `kubectl get pods -n gaiachain`         |

### 1.2. Configuración del cluster

```bash
kubectl create namespace castuo-prod
kubectl apply -f kubernetes/prod-rbac.yaml
kubectl run -n castuo-prod --rm -i --tty gaiachain-test --image=curlimages/curl -- \
  curl -s http://gaiachain-service.gaiachain:8080/health | jq
kubectl apply -f kubernetes/prod-storageclass.yaml
```

### 1.3. Activación con máxima seguridad

Políticas de seguridad de pod (PSP/PSS) y network policies:

```bash
# Políticas de seguridad (en 1.25+ el PSP puede fallar; usar solo el label del namespace)
kubectl apply -f kubernetes/security-policies.yaml
# Si el namespace ya existía sin label:
kubectl label namespace castuo-prod pod-security.kubernetes.io/enforce=restricted --overwrite

# Network policies estrictas para el coordinador FL
kubectl apply -f kubernetes/network-policies.yaml
```

Asegurar que los namespaces `monitoring` y `gaiachain` tengan las etiquetas `name: monitoring` y `name: gaiachain` para que las egress permitan el tráfico.

---

## 2. Generación de claves y secretos

### 2.1. Generación de claves de cifrado

Ejecutar en entorno seguro (recomendado air-gapped):

```bash
python -c "
from backend.security.end_to_end_encryption import EndToEndEncryption
import base64

e = EndToEndEncryption()
private_key, public_key = e.generate_key_pair()
kyber_public, kyber_private = e.pq_crypto._generate_kyber_keypair_raw()

with open('private-key.pem', 'wb') as f: f.write(private_key)
with open('public-key.pem', 'wb') as f: f.write(public_key)
with open('kyber-private.key', 'wb') as f: f.write(kyber_private)
with open('kyber-public.key', 'wb') as f: f.write(kyber_public)

print('Claves generadas correctamente:')
print(f'RSA Private: {len(private_key)} bytes')
print(f'RSA Public: {len(public_key)} bytes')
print(f'Kyber Private: {len(kyber_private)} bytes')
print(f'Kyber Public: {len(kyber_public)} bytes')
"
```

### 2.2. Creación de secrets en Kubernetes

```bash
kubectl create secret generic he-keys -n castuo-prod \
  --from-file=private-key.pem \
  --from-file=public-key.pem \
  --from-file=kyber-private.key \
  --from-file=kyber-public.key

kubectl get secret he-keys -n castuo-prod -o yaml
kubectl describe secret he-keys -n castuo-prod
```

### 2.3. Certificados TLS

```bash
kubectl apply -f kubernetes/prod-issuer.yaml
kubectl get clusterissuer
kubectl describe clusterissuer letsencrypt-prod
```

---

## 3. Despliegue de la infraestructura base

### 3.1. Dependencias (Helm)

```bash
helm upgrade --install rabbitmq bitnami/rabbitmq \
  --namespace castuo-prod \
  --version 11.12.0 \
  --values kubernetes/rabbitmq-values.yaml \
  --set auth.username=castuo \
  --set auth.password=$(openssl rand -hex 16) \
  --set auth.erlangCookie=$(openssl rand -hex 32)

helm upgrade --install prometheus prometheus-community/prometheus \
  --namespace castuo-prod \
  --version 19.7.2 \
  --values kubernetes/prometheus-values.yaml

helm upgrade --install grafana grafana/grafana \
  --namespace castuo-prod \
  --version 6.43.0 \
  --values kubernetes/grafana-values.yaml \
  --set adminPassword=$(openssl rand -hex 16)

kubectl get pods -n castuo-prod
```

### 3.2. Ingress

```bash
kubectl apply -f kubernetes/prod-ingress.yaml
kubectl get certificate -n castuo-prod
kubectl describe certificate castuo-prod-tls -n castuo-prod
```

---

## 4. Despliegue del sistema principal

### 4.1. ConfigMap y coordinador

```bash
kubectl apply -f kubernetes/prod-configmap.yaml
kubectl get configmap encryption-config -n castuo-prod -o yaml
```

### 4.2. Imagen y deployment

```bash
docker build -t ghcr.io/tu-organizacion/castuo-system:v2.1-prod -f backend/Dockerfile.prod .
docker push ghcr.io/tu-organizacion/castuo-system:v2.1-prod
kubectl apply -f kubernetes/prod-deployment.yaml
kubectl get pods -n castuo-prod -l app=secure-federated-coordinator
kubectl logs -n castuo-prod -l app=secure-federated-coordinator --tail=50 -f
```

### 4.3. Autoescalado y CronJobs

```bash
kubectl apply -f kubernetes/prod-hpa.yaml
kubectl apply -f kubernetes/prod-key-rotation-cronjob.yaml
kubectl apply -f kubernetes/prod-audit-cronjob.yaml
kubectl get hpa -n castuo-prod
kubectl get cronjobs -n castuo-prod
```

---

## 5. Verificación post-despliegue

### 5.1. Salud

```bash
kubectl get pods -n castuo-prod
kubectl port-forward -n castuo-prod svc/secure-federated-coordinator 8000:8000
curl -v http://localhost:8000/health
curl -v http://localhost:8000/ready
```

### 5.2. Funcionalidad

```bash
kubectl exec -n castuo-prod deploy/secure-federated-coordinator -- \
  python -m backend.scripts.migrate_to_he_federated_learning --test --models 5 --layers 3 --layer-size 50

kubectl exec -n castuo-prod deploy/secure-federated-coordinator -- \
  python -c "
from backend.compliance.immutable_traceability import ImmutableTraceability
from backend.security.end_to_end_encryption import EndToEndEncryption
e = EndToEndEncryption()
t = ImmutableTraceability(e)
print('Cadena verificada:', t.verify_chain())
print('Último evento:', t.current_chain[-1]['event']['type'] if t.current_chain else 'Ninguno')
"
```

### 5.3. Métricas y alertas

```bash
kubectl apply -f monitoring/prometheus/prod-alert-rules.yaml
kubectl get prometheusrules -n castuo-prod
kubectl port-forward -n castuo-prod svc/prometheus-server 9090:9090
# En http://localhost:9090 comprobar: fl_aggregation_latency_ms, fl_memory_usage_bytes, fl_models_per_second
```

### 5.4. Informe de auditoría

```bash
kubectl exec -n castuo-prod deploy/secure-federated-coordinator -- \
  python -m backend.scripts.generate_audit_report --period 7 --output /var/traceability/prod_audit_7days.json

kubectl cp castuo-prod/$(kubectl get pods -n castuo-prod -l app=secure-federated-coordinator -o jsonpath='{.items[0].metadata.name}'):/var/traceability/prod_audit_7days.json ./prod_audit_report.json
jq . prod_audit_report.json
```

---

## 6. Monitoreo y mantenimiento

- **Grafana**: `kubectl get secret -n castuo-prod grafana -o jsonpath='{.data.admin-password}' | base64 -d`  
  Importar dashboards desde `monitoring/grafana/dashboards/` (fl_performance, compliance, security).
- **Alertas**: Reglas en `monitoring/prometheus/prod-alert-rules.yaml` (HighFLLatency, LowFLThroughput, FLAggregationErrorRate).
- **Runbook**: [docs/PRODUCTION_RUNBOOK.md](PRODUCTION_RUNBOOK.md).
- **Onboarding de nodos**: [docs/NEW_NODE_ONBOARDING.md](NEW_NODE_ONBOARDING.md).

---

## 7. Checklist final de despliegue

| #  | Tarea                              | Comando / verificación                               | Estado |
|----|------------------------------------|------------------------------------------------------|--------|
| 1  | Crear namespace de producción      | `kubectl create namespace castuo-prod`              | ☐      |
| 2  | Configurar RBAC                    | `kubectl apply -f kubernetes/prod-rbac.yaml`         | ☐      |
| 3  | Generar claves de cifrado          | Script Python de generación                          | ☐      |
| 4  | Crear secrets de claves            | `kubectl create secret generic he-keys ...`          | ☐      |
| 5  | Desplegar dependencias             | Helm RabbitMQ, Prometheus, Grafana                   | ☐      |
| 6  | Configurar Ingress                 | `kubectl apply -f kubernetes/prod-ingress.yaml`      | ☐      |
| 7  | Aplicar ConfigMap                  | `kubectl apply -f kubernetes/prod-configmap.yaml`    | ☐      |
| 8  | Desplegar coordinador FL           | `kubectl apply -f kubernetes/prod-deployment.yaml`   | ☐      |
| 9  | Configurar HPA                     | `kubectl apply -f kubernetes/prod-hpa.yaml`          | ☐      |
| 10 | Configurar CronJobs                | Rotación de claves y auditorías                      | ☐      |
| 11 | Verificar salud de pods            | `kubectl get pods -n castuo-prod`                    | ☐      |
| 12 | Pruebas de funcionalidad           | Benchmark y trazabilidad                             | ☐      |
| 13 | Configurar alertas                 | `kubectl apply -f monitoring/prometheus/prod-alert-rules.yaml` | ☐ |
| 14 | Dashboards Grafana                 | Importar dashboards                                  | ☐      |
| 15 | Informe inicial de auditoría       | `generate_audit_report --period 7`                   | ☐      |
| 16 | Documentar configuración final     | Actualizar PRODUCTION_RUNBOOK.md si hay cambios      | ☐      |

---

## 8. Métricas de éxito post-despliegue

| Métrica                   | Objetivo | Verificación                         | Responsable   |
|---------------------------|----------|--------------------------------------|---------------|
| Tiempo agregación FL      | <50 ms   | `kubectl exec ... benchmark`         | Equipo IA     |
| Uso de memoria            | <1.8 Gi  | `kubectl top pod`                    | DevOps        |
| Tasa de éxito agregación  | >99.9 %  | Métricas / script                    | QA            |
| Latencia API              | <200 ms  | `curl -w "%{time_total}s" .../health`| DevOps        |
| Cobertura de cifrado      | 100 %    | `generate_audit_report`               | Seguridad     |
| Integración GaiaChain     | Sin errores | `kubectl logs -n gaiachain`        | Blockchain    |
| Rotación de claves        | Cada 90 días | `kubectl get cronjobs`             | Seguridad     |
| Informes de auditoría     | Según política | CronJob / manual                  | Cumplimiento  |

---

## 9. Procedimiento de rollback

### 9.1. Rollback a versión anterior

```bash
kubectl scale deployment/secure-federated-coordinator -n castuo-prod --replicas=0
kubectl set image deployment/secure-federated-coordinator -n castuo-prod coordinator=ghcr.io/tu-organizacion/castuo-system:v2.0-prod
kubectl scale deployment/secure-federated-coordinator -n castuo-prod --replicas=3
kubectl rollout status deployment/secure-federated-coordinator -n castuo-prod
kubectl logs -n castuo-prod -l app=secure-federated-coordinator --tail=50 -f
```

### 9.2. Restauración de datos (trazabilidad)

```bash
kubectl cp ./backups/backup_YYYYMMDD.json castuo-prod/$(kubectl get pods -n castuo-prod -l app=secure-federated-coordinator -o jsonpath='{.items[0].metadata.name}'):/var/traceability/restore.json
kubectl exec -n castuo-prod deploy/secure-federated-coordinator -- \
  python -m backend.scripts.restore_traceability_chain --file /var/traceability/restore.json
```

### 9.3. Verificación post-rollback

Comprobar `/health`, `/ready`, logs y métricas FL según [PRODUCTION_RUNBOOK.md](PRODUCTION_RUNBOOK.md).
