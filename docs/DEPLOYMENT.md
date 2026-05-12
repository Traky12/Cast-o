# Deployment Guide

## Alcance
Esta guia cubre despliegue y verificacion de CASTUO-SYSTEM en Kubernetes con foco en:
- API castuo-api
- HPA
- NetworkPolicy
- Validaciones CI/CD y tests

## Perfil de microservicios escalables

Se ha incorporado un perfil alineado con arquitectura de microservicios para operar en local (Docker Compose) y produccion (Kubernetes + Hetzner Terraform):

- Docker local: `docker-compose.microservices.yml`
- Kubernetes: `k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/hpa.yaml`, `k8s/ingress.yaml`, `k8s/configmap.yaml`
- Terraform Hetzner: `hetzner_infra/main.tf`, `hetzner_infra/variables.tf`, `hetzner_infra/outputs.tf`

### Microservicios incluidos en este perfil

- `castuo-api`
- `castuo-n8n`
- `castuo-prometheus`
- `castuo-grafana`

### Desarrollo local (perfil microservicios)

```bash
docker compose -f docker-compose.microservices.yml up -d --build
docker compose -f docker-compose.microservices.yml ps
```

Variables requeridas en `.env` para este perfil:

- `POSTGRES_PASSWORD`
- `N8N_BASIC_AUTH_USER`
- `N8N_BASIC_AUTH_PASSWORD`

### Produccion en Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.example.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

Comprobaciones clave:

```bash
kubectl get deploy,svc,hpa,ingress -n castuo-system
kubectl get pods -n castuo-system
kubectl describe hpa castuo-api-hpa -n castuo-system
kubectl describe hpa castuo-n8n-hpa -n castuo-system
```

## Prerrequisitos
- Cluster Kubernetes accesible
- Namespace castuo-system creado
- Ingress controller (ingress-nginx) instalado
- Metrics Server disponible para HPA

## Despliegue sobre Hetzner Cloud (produccion / demo Alex)

### Contexto de la infraestructura actual
El proyecto tiene desplegados dos servidores Ubuntu en Helsinki (hel1):

| Servidor | RAM | Uso recomendado |
|---|---|---|
| ubuntu-8gb-hel1-1 | 8 GB | produccion / demo completa |
| ubuntu-4gb-hel1-1 | 4 GB | staging / pruebas |

Cada servidor tiene 2 Primary IPs (IPv4 + IPv6), el firewall `firewall-1` aplicado y una zona DNS activa.

**Notas de estado (Hetzner, 1 abril 2026)**
- Object Storage en NBG1 degradado: irrelevante, los servidores usan hel1.
- Disponibilidad limitada de instancias cloud: no afecta a servidores ya creados.
- Easter holiday support (3-4 abril): soporte reducido; no crear ni destruir servidores esos dias.

---

### Reglas firewall-1 correctas (sincronizado con hetzner_infra/main.tf)

Reglas **Inbound** que deben estar activas en `firewall-1`:

| Puerto | Protocolo | Servicio | Estado requerido |
|--------|-----------|----------|-----------------|
| 22     | TCP       | SSH      | ✅ ya configurado |
| 80     | TCP       | HTTP / nginx proxy | ✅ ya configurado |
| 443    | TCP       | HTTPS    | ✅ ya configurado |
| 8000   | TCP       | API SABIONDA (FastAPI) | ✅ ya configurado |
| 5678   | TCP       | n8n workflows | ⚠️ **AÑADIR** — falta en el panel |
| 3000   | TCP       | Grafana dashboards | ⚠️ **AÑADIR** |
| 9090   | TCP       | Prometheus | ⚠️ **AÑADIR** |
| 8545   | TCP       | GaiaChain RPC | ⚠️ **AÑADIR** |

Reglas que deben **eliminarse**:

| Puerto | Motivo |
|--------|--------|
| 3306   | ❌ **ELIMINAR** — MySQL expuesto a internet es riesgo OWASP A05. No hay MySQL en el stack. |

> **IMPORTANTE — Puerto de n8n:**
> n8n usa el puerto `5678` (su puerto nativo). **NO cambiar a 5432**.
> El puerto 5432 es PostgreSQL — ponerle n8n en ese puerto provoca conflicto de datos
> y dejaría la base de datos inaccesible para toda la plataforma.

#### Pasos en el panel Hetzner para sincronizar el firewall

1. Ir a https://console.hetzner.cloud → **Firewalls** → `firewall-1` → **Rules**
2. **Eliminar** la regla inbound del puerto `3306`
3. **Añadir** las reglas inbound que faltan (una por una → Add rule):

```
TCP  5678  0.0.0.0/0 ::/0   # n8n workflows
TCP  3000  0.0.0.0/0 ::/0   # Grafana
TCP  9090  0.0.0.0/0 ::/0   # Prometheus
TCP  8545  0.0.0.0/0 ::/0   # GaiaChain RPC
```

4. Pulsar **Apply changes to 1 Server** al acabar

---

### Paso 1 — Obtener la IP publica

1. Acceder a https://console.hetzner.cloud
2. Ir a **Servers** → clic en `ubuntu-8gb-hel1-1` (produccion) o `ubuntu-4gb-hel1-1` (staging)
3. Copiar la **Public IPv4** mostrada en la ficha del servidor

---

### Paso 2 — Verificar la clave SSH local

La clave SSH debe estar subida previamente en Hetzner (`Security → SSH Keys`). Si aun no la tienes:

```powershell
# Generar (si no existe)
ssh-keygen -t ed25519 -C "castuo-hetzner" -f "$env:USERPROFILE\.ssh\hetzner_ed25519"

# Mostrar la clave publica para pegarla en el panel Hetzner:
Get-Content "$env:USERPROFILE\.ssh\hetzner_ed25519.pub"
```

---

### Paso 3 — Conexion SSH manual (PowerShell)

```powershell
$SERVER_IP = "89.167.5.233"   # ubuntu-8gb-hel1-1  (#118296333)  cax21 ARM64

# Conexion basica
ssh -i "$env:USERPROFILE\.ssh\id_rsa" root@$SERVER_IP

# O si usaste hetzner_ed25519:
ssh -i "$env:USERPROFILE\.ssh\hetzner_ed25519" root@$SERVER_IP
```

---

### Paso 4 — Despliegue automatico completo (un solo comando)

El script `Connect-Hetzner-Deploy.ps1` cubre SSH, clonado del repo, copia del .env,
`docker compose up --build` y health checks de todos los servicios:

```powershell
cd "C:\Users\traky\OneDrive - FCI\Castuo-system"

# Despliegue completo sobre el servidor de produccion (ubuntu-8gb-hel1-1 · cax21 · ARM64):
.\scripts\windows\Connect-Hetzner-Deploy.ps1 -ServerIP "89.167.5.233"

# Con .env local ya listo:
.\scripts\windows\Connect-Hetzner-Deploy.ps1 `
    -ServerIP   "89.167.5.233" `
    -EnvFile    "C:\Users\traky\.castuo.env" `
    -SshKeyPath "$env:USERPROFILE\.ssh\hetzner_ed25519"

# Solo verificacion sin redesplegar:
.\scripts\windows\Connect-Hetzner-Deploy.ps1 -ServerIP "89.167.5.233" -SkipDeploy
```

---

### Paso 5 — Health checks tras el despliegue

```powershell
$IP = "89.167.5.233"   # ubuntu-8gb-hel1-1  (#118296333)

# API SABIONDA
Invoke-RestMethod "http://${IP}:8000/health"
# {"status":"ok","agent":"SABIONDA","version":"3.0.0"}

# Catalogo de herramientas Claude
Invoke-RestMethod "http://${IP}:8000/api/v1/claude/tools"

# n8n - abrir en navegador
Start-Process "http://${IP}:5678"

# Grafana - abrir en navegador
Start-Process "http://${IP}:3000"

# Prometheus
Start-Process "http://${IP}:9090"
```

---

### Paso 6 — Configuracion DNS (zona ya creada)

Con la zona DNS activa en Hetzner (`DNS → castuo.es` o la zona que aparece en el dashboard),
añadir los registros A en https://dns.hetzner.com:

```
@     A   89.167.5.233    # dominio raiz  →  ubuntu-8gb-hel1-1
api   A   89.167.5.233    # api.tudominio.eu
n8n   A   89.167.5.233    # n8n.tudominio.eu
```

Verificar tras propagar (puede tardar hasta 5 minutos):

```powershell
.\scripts\windows\verify-dns-ssl.ps1 `
    -PrimaryDomain "tudominio.eu" `
    -N8nDomain     "n8n.tudominio.eu" `
    -HetznerIP     "89.167.5.233"
```

---

### Logs y diagnostico en tiempo real

```powershell
# Logs de todos los servicios
ssh root@89.167.5.233 "cd /opt/castuo-system && docker compose logs -f --tail=100"

# Solo la API
ssh root@89.167.5.233 "docker logs sabionda-api -f --tail=50"

# Estado de contenedores
ssh root@89.167.5.233 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

---

## Despliegue rapido local (PowerShell)
Este flujo sirve para levantar una demo local con Docker Compose en Windows. Usa este repositorio y no requiere Kubernetes.

```powershell
cd "C:\Users\traky\OneDrive - FCI\"
git clone https://github.com/Traky12/Castuo-system.git
cd Castuo-system
Copy-Item .env.example .env

# Rellenar antes las variables obligatorias del fichero .env
docker compose up -d --build
```

Si el repositorio ya esta clonado, basta con entrar en la carpeta, revisar .env y ejecutar el compose.

### Health check
```powershell
curl http://localhost:8000/health
```

Respuesta esperada actualmente:

```json
{"status":"ok","agent":"SABIONDA","version":"3.0.0"}
```

### Servicios publicados por el compose principal
- api en puerto 8000: FastAPI con endpoints de salud, IoT, SIEX, TRACES, PAC y catalogo Claude.
- n8n en puerto 5678: orquestacion de workflows.
- grafana en puerto 3000: dashboards y metricas.
- prometheus en puerto 9090: scraping y consultas de observabilidad.
- postgres en puerto 5432: base de datos PostgreSQL 16.
- openclaw-agente en puerto 8080: agente SABIONDA/OpenClaw.

### Endpoints demo validados
```text
http://localhost:8000/health
http://localhost:8000/api/v1/claude/tools
http://localhost:8000/api/v1/claude/context
http://localhost:5678
http://localhost:3000
```

### Notas de compatibilidad
- El compose principal no expone un proxy nginx en el puerto 80, por lo que las comprobaciones deben hacerse contra los puertos publicados por cada servicio.
- En el estado actual del repo no existen rutas publicas /agents, /sensors ni /blockchain/gaia en la API raiz. Para IoT, la ruta disponible es /api/v1/iot/telemetry.

## Aplicar manifests
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.example.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/networkpolicy.yaml
```

## Verificaciones operativas
```bash
kubectl get pods -n castuo-system
kubectl get deploy,svc,hpa,ingress -n castuo-system
kubectl describe hpa castuo-api-hpa -n castuo-system
kubectl get networkpolicy -n castuo-system
```

## Validacion de CI/CD
El workflow de referencia es .github/workflows/validate-all.yml y ejecuta:
- Tests JS
- Suite completa Python en tests/
- Cobertura Python (artifacts/coverage.xml)

## Rollback rapido
```bash
kubectl rollout undo deployment/castuo-api -n castuo-system
kubectl rollout status deployment/castuo-api -n castuo-system
```

## Recomendaciones de seguridad
- Sustituir secrets.example.yaml por secretos reales gestionados con Vault/SealedSecrets.
- Mantener NetworkPolicy activa y ajustar reglas por namespace/servicio segun topologia real.
- Revisar periodicamente limites/requests del Deployment y thresholds del HPA.
