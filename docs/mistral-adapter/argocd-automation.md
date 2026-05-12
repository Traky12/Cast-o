# Automatización con ArgoCD

Despliegue continuo y sincronizado en Hetzner: cero downtime, rollback automático, trazabilidad.

---

## Validación rápida después del setup

1. **Hacer push a `main`** para probar el workflow de GitHub Actions (`.github/workflows/argocd-sync.yml`).
2. **Revisar ArgoCD** en la interfaz web y confirmar que la aplicación está **Synced** y **Healthy**.

Para despliegue en **varios clusters** (EU, LATAM, Asia), ver [Arquitectura Multi-Cluster](argocd-multi-cluster.md).

---

## Resumen: qué vamos a automatizar

| Componente | Objetivo | Beneficio |
|------------|----------|-----------|
| **ArgoCD** | Despliegue continuo y sincronizado en Hetzner. | Cero downtime, rollback automático, trazabilidad. |
| **Repositorio Git** | Fuente de verdad para la configuración (Kustomize/Helm). | Infraestructura como código (IaC). |
| **Hetzner Cloud** | Entorno de producción (CX21: 2 vCPUs, 4GB RAM). | Escalable y económico. |
| **Prometheus + Grafana** | Monitorización integrada en ArgoCD. | Alertas en tiempo real (ej: CPU > 70%). |
| **RPi 500+ sensores** | Configuración automatizada para edge computing. | Despliegue consistente en todas las RPis. |
| **MkDocs + Mermaid** | Documentación auto-desplegada al actualizar. | Siempre actualizada. |

---

## Paso 1: Configurar ArgoCD en Hetzner

*Instalación en un servidor dedicado o en el mismo cluster de producción*

### 1.1 Crear un cluster Kubernetes en Hetzner

Usaremos k3s (ligero y compatible con ArgoCD):

```bash
# En tu servidor Hetzner (CX21 o superior):
curl -sfL https://get.k3s.io | sh -
# Verificar que el cluster está listo:
kubectl get nodes
```

Salida esperada:

```
NAME           STATUS   ROLES                  AGE   VERSION
hetzner-node   Ready    control-plane,master   1m    v1.25.x+k3s1
```

### 1.2 Instalar ArgoCD

```bash
# Crear namespace para ArgoCD
kubectl create namespace argocd
# Instalar ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
# Exponer el servicio (para acceso web)
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
# Obtener la IP pública de ArgoCD
kubectl get svc -n argocd
```

Salida esperada (ejemplo):

```
NAME                  TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)
argocd-server         LoadBalancer   10.43.123.123   123.123.123.123  80:30080/TCP,443:30443/TCP
```

### 1.3 Acceder a la interfaz de ArgoCD

- **URL:** `http://<EXTERNAL-IP>:80` (ej: http://123.123.123.123:80)
- **Usuario inicial:** `admin`
- **Contraseña inicial:** obtener con:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

---

## Paso 2: Configurar el Repositorio Git para ArgoCD

*Estructura recomendada en el repositorio castuo-system*

```
castuo-system/
├── .github/
│   └── workflows/
│       └── argocd-sync.yml   # GitHub Action para sincronizar con ArgoCD
├── kubernetes/
│   ├── base/                 # Configuración base (Kustomize)
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── overlays/
│   │   ├── staging/
│   │   │   └── kustomization.yaml
│   │   └── production/
│   │       ├── kustomization.yaml
│   │       └── deployment-patch.yaml
│   └── prometheus/
│       ├── prometheus.yaml
│       ├── grafana.yaml
│       └── alert-rules.yaml
├── docs/
├── scripts/
│   └── salud-verificacion.sh
```

La configuración base y overlays están en el repo:

- **Base:** `kubernetes/base/` (namespace, deployment castuo-backend, service)
- **Producción:** `kubernetes/overlays/production/` (configMapGenerator con PORT_HIDRO, DB_URL, MQTT_*; deployment-patch)
- **Staging:** `kubernetes/overlays/staging/` (1 réplica, menos recursos)
- **Monitorización:** `kubernetes/prometheus/` (Grafana + datasource Prometheus; Prometheus Operator opcional)

---

## Paso 3: Configurar Aplicaciones en ArgoCD

*Desde la interfaz web o con argocd CLI*

### 3.1 Añadir el Repositorio Git

1. En la interfaz de ArgoCD: **Settings → Repositories**
2. **Connect Repo** y añadir:
   - **URL:** `https://github.com/tu-usuario/castuo-system.git`
   - **Usuario/Contraseña:** usar un Personal Access Token (PAT) de GitHub

### 3.2 Crear una Aplicación para Producción

1. **New App**
2. Configurar:
   - **Application Name:** `castuo-system-production`
   - **Project:** default
   - **Sync Policy:** Automatic
   - **Repository URL:** `https://github.com/tu-usuario/castuo-system.git`
   - **Revision:** HEAD (o tag `v1.4.0`)
   - **Path:** `kubernetes/overlays/production`
   - **Cluster URL:** `https://kubernetes.default.svc`
   - **Namespace:** `castuo-system`
3. **Create**

---

## Paso 4: Integrar Prometheus y Grafana con ArgoCD

*Monitorización centralizada*

- Añadir en ArgoCD una aplicación **castuo-monitoring**
- **Path:** `kubernetes/prometheus`
- Los manifiestos `prometheus.yaml` y `grafana.yaml` (y opcionalmente `alert-rules.yaml`) están en el repo. Si usas Prometheus Operator, el CRD `Prometheus` de `monitoring.coreos.com/v1` debe estar instalado en el cluster.

**Alerta de ejemplo (CPU > 70%):** ver `kubernetes/prometheus/alert-rules.yaml`.

---

## Paso 5: Automatizar con GitHub Actions

*Sincronización automática al hacer push a main*

El workflow `.github/workflows/argocd-sync.yml`:

- Se dispara en `push` a `main`
- Instala ArgoCD CLI, hace login con secrets y ejecuta `argocd app sync castuo-system-production` y `argocd app wait --health`

**Secrets en GitHub (Settings → Secrets → Actions):**

- `ARGOCD_SERVER`: URL de ArgoCD (ej: `123.123.123.123:80`)
- `ARGOCD_USERNAME`: `admin`
- `ARGOCD_PASSWORD`: contraseña obtenida en el Paso 1.3

---

## Paso 6: Validar y Monitorizar

### 6.1 Estado en ArgoCD

En la interfaz de ArgoCD comprobar:

- **Health Status:** Healthy
- **Sync Status:** Synced

### 6.2 Prometheus y Grafana

- **Prometheus:** http://&lt;EXTERNAL-IP&gt;:9090
- **Grafana:** http://&lt;EXTERNAL-IP&gt;:3000 (admin / admin)
  - Data source Prometheus: `http://prometheus-server:9090`
  - Importar dashboard **10600** ("Docker and System Monitoring")

### 6.3 Script de salud

```bash
# En el servidor de producción:
chmod +x scripts/salud-verificacion.sh
./scripts/salud-verificacion.sh
```

Salida esperada:

- ✅ Fase 1: Health endpoint 200 OK
- ✅ Fase 2: Hidroponía → 500 sensores (NFT 288 lechugas)
- ✅ Fase 4: ROOT MAESTRO
- ✅ Fase 5: Documentación lista

---

[Volver a Deploy](deploy.md) · [Arquitectura](arquitectura-dehesas-edge.md)
