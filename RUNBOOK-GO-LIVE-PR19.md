# RUNBOOK — Go-Live PR19: Frontend + Backend Operativo en Hetzner

**CASTÚO-SYSTEM™ v3.1** · Fecha: 2026-04-02  
Autor: Arquitectura europea soberana  
Aplicable a: `castuo-system.cloud` (Hetzner K3s / Hetzner Cloud)

---

## Resumen de cambios PR19

| Fichero | Cambio |
|---|---|
| `k8s/ingress.yaml` | **FIX CRÍTICO:** ClusterIssuer `letsencrypt-production` → `letsencrypt-prod`; 4 dominios TLS; ingress renombrado a `castuo-ingress` |
| `k8s/ingress-no-frontend.yaml` | Variante sin frontend: raíz/www → API (fallback) |
| `k8s/frontend-service.yaml` | Deployment + Service frontend (nginx:80) + n8n (5678→80) |
| `frontend/index.html` | Panel de control con health checks y probador de endpoints |
| `frontend/nginx.dev.conf` | Proxy nginx dev (3000 → api:8000) |
| `docker-compose.dev.yml` | Entorno de desarrollo local (frontend + API + InfluxDB + MQTT) |
| `Makefile` | Comandos: `make dev`, `make test-smoke`, `make k8s-apply`, etc. |

---

## Arquitectura de red

```
Internet
   │
   ▼
Cloudflare (WAF + CDN) — opcional
   │
   ▼
Hetzner LB → nginx Ingress Controller (K3s)
   │
   ├── castuo-system.cloud      → castuo-frontend-service:80 (nginx → HTML panel)
   ├── www.castuo-system.cloud  → castuo-frontend-service:80 (redirect a raíz)
   ├── api.castuo-system.cloud  → castuo-api-service:80      (FastAPI :8000)
   └── n8n.castuo-system.cloud  → castuo-n8n-service:80      (n8n :5678)
```

> **Nota técnica de puertos:** En este repo los Services exponen puerto **80**
> (targetPort al pod). El Ingress enruta al puerto del Service (80), no al puerto
> del Pod. No usar `port: 8000` o `port: 5678` en las reglas del Ingress.

---

## Paso 0: Verificar prerrequisitos

```bash
# 1. Conectar al cluster Hetzner
hcloud kubeconfig create castuo-prod --output kubeconfig.yaml
export KUBECONFIG=$(pwd)/kubeconfig.yaml

# 2. Comprobar conectividad
kubectl cluster-info

# 3. Verificar cert-manager instalado
kubectl get pods -n cert-manager
# Debe haber: cert-manager, cert-manager-cainjector, cert-manager-webhook → Running

# Si NO está instalado:
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=90s

# 4. Verificar nginx Ingress Controller
kubectl get pods -n ingress-nginx
# O en K3s: kubectl get pods -n kube-system -l app=svclb-traefik (si usa Traefik en su lugar)
```

---

## Paso 1: DNS — Apuntar dominios al LB de Hetzner

```bash
# Obtener IP del LoadBalancer
LB_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "LB IP: $LB_IP"

# Verificar resolución (esperar propagación DNS — puede tardar hasta 48h)
dig +short castuo-system.cloud
dig +short api.castuo-system.cloud
dig +short n8n.castuo-system.cloud

# Todos deben devolver la misma IP: $LB_IP
```

**Configuración DNS requerida en tu proveedor (Arsys / Cloudflare):**

| Tipo | Host | Valor | TTL |
|------|------|-------|-----|
| A | `@` (castuo-system.cloud) | `$LB_IP` | 300 |
| A | `www` | `$LB_IP` | 300 |
| A | `api` | `$LB_IP` | 300 |
| A | `n8n` | `$LB_IP` | 300 |

---

## Paso 2: Desplegar manifiestos

### Opción A: Con frontend dedicado (recomendado para PR19)

```bash
# Namespace y configuración base
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/cluster-issuer.yaml
kubectl apply -f k8s/configmap.yaml

# Secrets (si no existen ya)
kubectl create secret generic castuo-secrets \
  --namespace=castuo-system \
  --from-literal=JWT_SECRET="$(openssl rand -hex 32)" \
  --from-literal=GAIACHAIN_PRIVATE_KEY="0x$(openssl rand -hex 32)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Servicios y deployments
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/frontend-service.yaml   # incluye frontend + n8n Service
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/hpa.yaml

# Ingress con frontend en raíz
kubectl apply -f k8s/ingress.yaml

# Verificar rollout
kubectl rollout status deployment/castuo-api      -n castuo-system --timeout=120s
kubectl rollout status deployment/castuo-frontend  -n castuo-system --timeout=60s || true
```

### Opción B: Sin frontend (API en raíz como fallback)

```bash
# Si castuo-frontend-service NO está desplegado, usar:
kubectl apply -f k8s/ingress-no-frontend.yaml
# El mismo nombre "castuo-ingress" → sobrescribe el anterior sin borrar los Secrets TLS
```

---

## Paso 3: Verificar certificados TLS

```bash
# Estado de los certificados (cert-manager los crea automáticamente)
kubectl get certificate -n castuo-system
# Debe mostrar: READY=True para castuo-root-tls, castuo-api-tls, castuo-n8n-tls

# Si no están listos (ACME challenge pendiente):
kubectl describe certificate castuo-root-tls -n castuo-system
kubectl get challenge -A

# Si el challenge falla: verificar que DNS ya apunta al LB y que puerto 80 está abierto
# ACME HTTP-01 necesita acceso HTTP al dominio para validar.

# Forzar renovación si está atascado:
kubectl delete certificate castuo-root-tls castuo-api-tls castuo-n8n-tls -n castuo-system
kubectl apply -f k8s/ingress.yaml   # cert-manager los recrea automáticamente
```

---

## Paso 4: Validaciones DNS y TLS

```bash
# ── DNS ──────────────────────────────────────────────────────────────────────
dig +short castuo-system.cloud
dig +short api.castuo-system.cloud
dig +short n8n.castuo-system.cloud
# Todos deben devolver $LB_IP

nslookup api.castuo-system.cloud
# Address: <LB_IP>

# ── TLS ──────────────────────────────────────────────────────────────────────
for domain in castuo-system.cloud api.castuo-system.cloud n8n.castuo-system.cloud; do
  echo "=== $domain ==="
  echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null \
    | openssl x509 -noout -subject -dates
  echo ""
done

# O con make:
make k8s-tls
```

---

## Paso 5: Smoke tests de usabilidad

```bash
# ── Frontend raíz ────────────────────────────────────────────────────────────
curl -I https://castuo-system.cloud/
# HTTP/2 200 + Strict-Transport-Security header

# ── API ──────────────────────────────────────────────────────────────────────
curl -sf https://api.castuo-system.cloud/health | python3 -m json.tool
# {"status": "ok", "version": "3.1.x", ...}

# ── API Docs (Swagger UI) ────────────────────────────────────────────────────
curl -sf -o /dev/null -w "%{http_code}" https://api.castuo-system.cloud/docs
# 200

# ── SABIONDA IA ──────────────────────────────────────────────────────────────
curl -sf https://api.castuo-system.cloud/api/v1/claude/status | python3 -m json.tool

# ── Auditoría inmutable ──────────────────────────────────────────────────────
curl -sf https://api.castuo-system.cloud/api/v1/audit/actions | python3 -m json.tool

# ── Seguridad: tenant inválido → 403 ─────────────────────────────────────────
curl -sf -w "\nHTTP: %{http_code}\n" \
  -H "X-Tenant-ID: tenant-inexistente" \
  https://api.castuo-system.cloud/api/v1/tenants/current
# HTTP: 403

# ── n8n ──────────────────────────────────────────────────────────────────────
curl -I https://n8n.castuo-system.cloud/healthz
# HTTP/2 200
```

---

## Paso 6: Validación local antes de desplegar

```bash
# Levantar entorno local completo
make dev
# → Frontend panel: http://localhost:3000
# → API Swagger:    http://localhost:8000/docs

# En otra terminal: smoke tests locales
make test-smoke

# Tests unitarios + integración completos
make test-full
# Resultado esperado: 287 passed, 2 skipped
```

---

## Troubleshooting

### El certificado TLS no se crea (READY=False)

```bash
# 1. Verificar el ClusterIssuer (PR19 fix: era "letsencrypt-production")
kubectl get clusterissuer letsencrypt-prod -o yaml
# name debe ser "letsencrypt-prod"

# 2. Ver eventos del certificado
kubectl describe certificate castuo-api-tls -n castuo-system

# 3. Ver challenge
kubectl get challenge -A
kubectl describe challenge -A | grep -A20 "Status:"

# Causa más común: DNS no apunta aún al LB o puerto 80 bloqueado por firewall.
```

### Frontend devuelve 503

```bash
# Verificar que el Deployment está corriendo
kubectl get pods -n castuo-system -l app=castuo-frontend

# Si el pod no existe: desplegar con Option B (sin frontend) como fallback
kubectl apply -f k8s/ingress-no-frontend.yaml
```

### API devuelve 502 / 503

```bash
kubectl get pods -n castuo-system -l app=castuo-api
kubectl describe pod -n castuo-system -l app=castuo-api | grep -A10 "Events:"
kubectl logs -n castuo-system -l app=castuo-api --tail=50
```

### n8n no responde

```bash
# Verificar que el PVC está disponible
kubectl get pvc castuo-n8n-pvc -n castuo-system

# n8n tarda en arrancar la primera vez (30-60s)
kubectl rollout status deployment/castuo-n8n -n castuo-system --timeout=90s
kubectl logs -n castuo-system -l app=castuo-n8n --tail=30
```

### Secretos faltantes

```bash
# Crear secretos mínimos necesarios
kubectl create secret generic castuo-secrets \
  --namespace=castuo-system \
  --from-literal=JWT_SECRET="$(openssl rand -hex 32)" \
  --from-literal=GAIACHAIN_PRIVATE_KEY="0x$(openssl rand -hex 32)" \
  --from-literal=N8N_ENCRYPTION_KEY="$(openssl rand -hex 32)" \
  --from-literal=N8N_USER=admin \
  --from-literal=N8N_PASSWORD="$(openssl rand -hex 16)" \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

## Checklist de Go-Live

```
[ ] DNS propagado: dig +short castuo-system.cloud = <LB_IP>
[ ] DNS propagado: dig +short api.castuo-system.cloud = <LB_IP>
[ ] DNS propagado: dig +short n8n.castuo-system.cloud = <LB_IP>
[ ] TLS: certificate READY=True para castuo-root-tls
[ ] TLS: certificate READY=True para castuo-api-tls
[ ] TLS: certificate READY=True para castuo-n8n-tls
[ ] HTTP→HTTPS redirect funciona (curl -I http://castuo-system.cloud/)
[ ] GET https://castuo-system.cloud/ → 200 (panel frontend)
[ ] GET https://api.castuo-system.cloud/health → {"status":"ok"}
[ ] GET https://api.castuo-system.cloud/docs → 200 (Swagger UI)
[ ] GET https://api.castuo-system.cloud/api/v1/claude/status → 200
[ ] GET https://api.castuo-system.cloud/api/v1/audit/actions → 200
[ ] GET https://n8n.castuo-system.cloud/healthz → 200
[ ] X-Tenant-ID inválido → 403 (multi-tenancy activo)
[ ] HPA activo: kubectl get hpa -n castuo-system
[ ] Pods estables: 0 restarts en últimos 5 minutos
```

---

## Comandos de referencia rápida (cheatsheet)

```bash
# Estado global
make k8s-status

# TLS de los 4 dominios
make k8s-tls

# Logs API en vivo
make k8s-logs

# Smoke tests en producción
make test-prod

# Escalar API manualmente
kubectl scale deployment castuo-api --replicas=5 -n castuo-system

# Forzar redeploy (sin cambio de imagen)
kubectl rollout restart deployment/castuo-api -n castuo-system
```
