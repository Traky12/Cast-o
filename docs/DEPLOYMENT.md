# CASTÚO-SYSTEM™ v3.1 — Guía de Despliegue

## Requisitos Previos

| Componente | Versión mínima | Notas |
|------------|---------------|-------|
| Python | 3.11 | Para tests y API |
| Docker | 24.x | Para contenedores |
| kubectl | 1.28+ | Para Kubernetes |
| Helm | 3.12+ | Para Prometheus/Grafana |
| Hetzner Cloud CLI (`hcloud`) | 1.40+ | Para cluster K8s |

---

## 1. Despliegue Local (Desarrollo)

```bash
# Clonar y preparar entorno
git clone https://github.com/traky12/castuo-system.git
cd castuo-system
cp .env.example .env
# Editar .env con tus valores

# Instalar dependencias Python
pip install -r api/requirements.txt

# Ejecutar tests
pytest tests/ -v

# Arrancar todos los servicios
docker compose up -d

# Verificar
curl http://localhost:8000/health
```

**Servicios disponibles en local:**

| Servicio | URL |
|---------|-----|
| FastAPI | http://localhost:8000 |
| FastAPI Docs | http://localhost:8000/docs |
| n8n | http://localhost:5678 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| LangGraph | http://localhost:8200 |

---

## 2. Despliegue en Hetzner Kubernetes

### 2.1 Crear el Cluster

```bash
# Instalar Hetzner Cloud CLI
curl -sfL https://install.hetzner.com/hcloud | bash

# Login
hcloud auth login

# Crear cluster (ejemplo: 3 nodos CX21)
hcloud k8s cluster create \
  --name castuo-prod \
  --location nbg1 \
  --node-pool-name workers \
  --node-pool-node-type cx21 \
  --node-pool-count 3

# Obtener kubeconfig
hcloud k8s cluster get-kubeconfig castuo-prod > ~/.kube/config
kubectl get nodes
```

### 2.2 Instalar Pre-requisitos en el Cluster

```bash
# 1. ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.loadBalancerIP="TU_IP_HETZNER"

# 2. Cert-Manager (TLS automático)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app=cert-manager \
  -n cert-manager --timeout=120s

# 3. ClusterIssuer para Let's Encrypt
kubectl apply -f k8s/cluster-issuer.yaml
kubectl describe clusterissuer letsencrypt-prod

# 4. Prometheus + Grafana (stack completo)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword="TU_GRAFANA_PASSWORD" \
  --set grafana.sidecar.dashboards.enabled=true \
  --set grafana.sidecar.dashboards.searchNamespace=ALL
```

### 2.3 Crear Secrets en el Cluster

```bash
# Opción A: Desde fichero (NO subir a Git)
cp k8s/secrets.example.yaml k8s/secrets.yaml
# Editar k8s/secrets.yaml con valores base64:
echo -n "TU_JWT_SECRET"       | base64  # → JWT_SECRET
echo -n "0xTU_CLAVE_PRIVADA"  | base64  # → GAIACHAIN_PRIVATE_KEY
echo -n "TU_DB_PASSWORD"      | base64  # → DB_PASSWORD

kubectl apply -f k8s/secrets.yaml -n castuo-system

# Opción B: Directamente con kubectl (recomendado en CI)
kubectl create secret generic castuo-secrets \
  --namespace=castuo-system \
  --from-literal=JWT_SECRET="TU_JWT_SECRET" \
  --from-literal=GAIACHAIN_PRIVATE_KEY="0xTU_CLAVE" \
  --from-literal=DB_PASSWORD="TU_DB_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 2.4 Desplegar con el Script

```bash
# Despliegue completo (idempotente)
./scripts/kubectl-deploy.sh

# Solo verificar estado
./scripts/kubectl-deploy.sh --check

# Rollback si algo falla
./scripts/kubectl-deploy.sh --rollback
```

### 2.5 Verificar el Despliegue

```bash
# Estado de recursos
kubectl get pods,services,ingress,hpa,pvc -n castuo-system

# Logs en tiempo real
kubectl logs -f -n castuo-system -l app=castuo-api

# Healthcheck externo
curl -I https://api.castuo-system.cloud/health

# Validar TLS
echo | openssl s_client -connect api.castuo-system.cloud:443 2>/dev/null \
  | openssl x509 -noout -dates
```

---

## 3. CI/CD con GitHub Actions

### 3.1 Configurar Secrets en GitHub

Ve a **Settings → Secrets → Actions** y añade:

| Secret | Cómo generarlo |
|--------|---------------|
| `HETZNER_KUBECONFIG` | `cat ~/.kube/config \| base64` |
| `JWT_SECRET_KEY` | `openssl rand -hex 32` |
| `GAIACHAIN_PRIVATE_KEY` | Tu clave privada `0x...` |
| `DB_PASSWORD` | Contraseña segura |
| `MISTRAL_API_KEY` | Desde console.mistral.ai |
| `SABIONDA_API_KEY` | Desde tu cuenta SABIONDA |

### 3.2 Workflows Disponibles

| Workflow | Trigger | Descripción |
|---------|---------|-------------|
| `ci.yml` | push/PR a `main` | Validación JSON, sintaxis Python, tests básicos |
| `deploy.yml` | push a `main` | Tests completos → SAST → Docker push → SSH deploy |
| `deploy-to-hetzner.yml` | push a `main` / manual | Tests → Docker push → `kubectl apply` completo |
| `deploy-hetzner-staging.yml` | push a `main` | Deploy a entorno staging |

### 3.3 Lanzar Deploy Manual

```bash
# Requires GitHub CLI (gh)
gh workflow run deploy-to-hetzner.yml --ref main

# Con tag de imagen específico
gh workflow run deploy-to-hetzner.yml --ref main \
  -f image_tag=sha-abc1234
```

---

## 4. Monitoreo

### 4.1 Grafana

```bash
# Port-forward si no tienes Ingress de monitoring
kubectl port-forward -n monitoring svc/kube-prometheus-grafana 3000:80

# Importar dashboard de CASTÚO
# Ve a Grafana → Dashboards → Import
# Sube: monitoring/grafana/dashboards/castuo-api.json
```

**Paneles incluidos:**
- Pods en ejecución (verde/amarillo/rojo por umbral)
- CPU y RAM (gauges con umbrales de alerta)
- Réplicas HPA actuales
- Request rate por endpoint (req/s)
- Latencia p50/p95/p99 (ms)
- Errores HTTP 4xx/5xx
- Transacciones GaiaChain / hora
- Lotes validados / hora

### 4.2 Alertas Prometheus

Las alertas están en `monitoring/prometheus/rules/`. Se activan para:
- Pod caído > 1 minuto
- CPU > 85% sostenido > 5 minutos
- RAM > 90% sostenido > 5 minutos
- Errores HTTP 5xx > 5% en 5 minutos
- HPA al máximo de réplicas
- PVC lleno > 85%

Ver `monitoring/prometheus/rules/castuo_k8s_alerts.yml` para la configuración completa.

---

## 5. Backups

```bash
# Backup manual del PVC de datos
./scripts/backup.sh

# Backup automático (añadir a crontab)
# 0 2 * * * /opt/castuo-system/scripts/backup.sh >> /var/log/castuo-backup.log 2>&1
```

Los backups se guardan en `/backups/castuo/` con retención de 30 días.

---

## 6. WordPress Plugin

1. Subir `wp-content/plugins/castuo-validar-lote/` al servidor WordPress
2. Activar el plugin desde **Plugins → Activar**
3. Configurar en **Ajustes → CASTÚO API**:
   - URL de la API: `https://api.castuo-system.cloud`
   - JWT Secret: el mismo valor que `JWT_SECRET_KEY`
4. Añadir shortcode a cualquier página:
   ```
   [castuo_validar_lote]
   ```
5. O usar la plantilla de página **Panel Operador** (`page-operador.php`)

---

## 7. Solución de Problemas

### Pods en CrashLoopBackOff
```bash
kubectl describe pod -n castuo-system $(kubectl get pod -n castuo-system -l app=castuo-api -o name | head -1)
kubectl logs -n castuo-system -l app=castuo-api --previous
```

### TLS no emitido
```bash
kubectl describe certificaterequest -n castuo-system
kubectl describe order -n castuo-system
# Verificar que el ClusterIssuer esté Ready:
kubectl get clusterissuer letsencrypt-prod
```

### GaiaChain en estado `misconfigured`
```bash
# Verificar que las variables están en el secret
kubectl get secret castuo-secrets -n castuo-system -o json \
  | python3 -c "import json,sys,base64; d=json.load(sys.stdin); \
    [print(k,'→',base64.b64decode(v).decode()[:8]+'...') for k,v in d['data'].items()]"
```

### Rollback de imagen Docker
```bash
# Ver historial de deployments
kubectl rollout history deployment/castuo-api -n castuo-system

# Volver a la versión anterior
kubectl rollout undo deployment/castuo-api -n castuo-system

# O al script
./scripts/kubectl-deploy.sh --rollback
```
