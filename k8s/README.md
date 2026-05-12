# 📂 Kubernetes Manifests para CASTÚO-SYSTEM™

Este directorio contiene los **manifestos de Kubernetes** para desplegar **CASTÚO-SYSTEM™** en producción (Hetzner CX22).

---

## 📌 Archivos principales

| **Archivo** | **Descripción** | **Dependencias** |
|-------------|-----------------|------------------|
| `namespace.yaml` | Crea el namespace `castuo-system`. | — |
| `configmap.yaml` | Configuración no sensible (variables de entorno públicas). | — |
| `secrets.example.yaml` | Plantilla para crear secrets (**no subir con datos reales**). | `kubectl create -f` |
| `deployment.yaml` | Despliegue de la API (FastAPI) + n8n. | `configmap.yaml`, `castuo-secrets`, `regcred` |
| `service.yaml` | Expone los servicios (API, n8n, frontend). | `deployment.yaml` |
| `ingress.yaml` | Configura el Ingress para HTTPS (Let's Encrypt). | `service.yaml`, `cluster-issuer.yaml` |
| `pvc.yaml` | Persistent Volume Claim para PostgreSQL. | — |
| `hpa.yaml` | Horizontal Pod Autoscaler (3–10 réplicas). | `deployment.yaml` |
| `networkpolicy.yaml` | Políticas de red para aislar el namespace. | `namespace.yaml` |
| `cluster-issuer.yaml` | Configuración de Let's Encrypt para certificados SSL. | cert-manager instalado |

## 📌 Archivos adicionales

| **Archivo** | **Descripción** |
|-------------|-----------------|
| `redis-deployment.yaml` | Despliegue de Redis (caché y colas). |
| `tenant-template.yaml` | Plantilla de tenant para arquitectura multi-tenancy. |
| `prometheus-rules.yaml` | Reglas de alertas para Prometheus. |
| `gdpr-cronjob.yaml` | CronJob de limpieza de datos conforme a GDPR. |
| `timescale-ha.yaml` | Despliegue de TimescaleDB en alta disponibilidad. |
| `agroedu-deployment.yaml` | Despliegue del módulo AgroEdu. |
| `agroedu-ingress.yaml` | Ingress del módulo AgroEdu. |
| `agroedu-monitoring.yaml` | Monitorización del módulo AgroEdu. |
| `frontend-service.yaml` | Servicio del frontend. |

---

## 🚀 Cómo Aplicar los Manifestos

### Orden recomendado

```bash
# 1. Namespace
kubectl apply -f namespace.yaml

# 2. Configuración base
kubectl apply -f configmap.yaml

# 3. Secrets (usar la plantilla como referencia, NO aplicar con datos de ejemplo)
# kubectl apply -f secrets.example.yaml

# 4. Almacenamiento
kubectl apply -f pvc.yaml

# 5. Aplicación
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# 6. Autoescalado y red
kubectl apply -f hpa.yaml
kubectl apply -f networkpolicy.yaml

# 7. Certificados SSL
kubectl apply -f cluster-issuer.yaml
```

> **Nota:** En CI/CD el workflow `.github/workflows/deploy-to-hetzner.yml` aplica los manifestos automáticamente en el orden correcto.

---

## 🔍 Verificaciones

```bash
# Estado de todos los recursos
kubectl get deploy,svc,hpa,ingress,networkpolicy -n castuo-system

# Pods
kubectl get pods -n castuo-system

# HPA
kubectl describe hpa castuo-api-hpa -n castuo-system
```

---

## 🛠️ Resolución de Problemas

| Problema | Causa | Solución |
|---|---|---|
| `ImagePullBackOff` | Falta `imagePullSecrets` o credenciales del registry incorrectas. | Verifica que `regcred` exista: `kubectl get secret regcred -n castuo-system` y que `imagePullSecrets` esté configurado en `deployment.yaml`. |
| `CrashLoopBackOff` | Error en la aplicación (ej. falta una variable de entorno). | Revisa los logs: `kubectl logs deployment/castuo-api -n castuo-system --previous` |
| `Pending` (sin nodo) | Recursos insuficientes en el clúster. | Escala el clúster en Hetzner o reduce `resources.requests` en `deployment.yaml`. |
| Certificado SSL no emitido | cert-manager no instalado o `ClusterIssuer` no aplicado. | `kubectl apply -f cluster-issuer.yaml` y verifica cert-manager: `kubectl get pods -n cert-manager`. |

---

## 📚 Referencias

- [docs/HETZNER-K8S-DEPLOY.md](../docs/HETZNER-K8S-DEPLOY.md) — Guía completa de despliegue en producción.
- [docs/hetzner-prod-secrets.md](../docs/hetzner-prod-secrets.md) — Secrets requeridos y cómo obtenerlos.
- Workflow CI/CD: `.github/workflows/deploy-to-hetzner.yml`
