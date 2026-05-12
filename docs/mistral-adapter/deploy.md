# Deploy en producción (Hetzner)

Despliegue unificado: **api-jeremie** (Mistral) en **8000** y **backend** (Cooperativas) en **8001**.

## Runbook completo (copiar/pegar)

```bash
# 1. Clonar y configurar
git clone https://github.com/castuo-system/platform.git
cd platform
cp .env.example .env
# Editar .env (ej: PORT_HIDRO=8002, DB_URL=postgresql://...)

# 2. Instalar mermaid2 (si no está instalado)
pip install mkdocs-mermaid2-plugin

# 3. Construir y desplegar
docker compose -f docker-compose.hetzner.yml build
docker compose -f docker-compose.hetzner.yml --profile hidroponia up -d

# 4. Verificar salud
chmod +x salud-verificacion.sh
./salud-verificacion.sh

# 5. Publicar documentación
mkdocs gh-deploy --message "v1.4.0: Arquitectura Dehesas→Edge + Verificación Salud 10/10 + RPi 500+"

# 6. Validar métricas
docker stats rpi-hidroponia
k6 run load_test.js
```

## Build & Deploy (rápido)

```bash
docker compose -f docker-compose.hetzner.yml up -d --build
```

## Publicar documentación (MkDocs)

```bash
pip install mkdocs-mermaid2-plugin
mkdocs gh-deploy --message "v1.4.0: Arquitectura Dehesas→Edge + Verificación Salud 10/10"
# Con RPi 500+:
mkdocs gh-deploy --message "v1.4.0: Arquitectura Dehesas→Edge + Verificación Salud 10/10 + RPi 500+"
```

**URL pública:** `https://tudominio.com/arquitectura-dehesas-edge`

## Validación

```bash
curl http://localhost:8000/mistral/health
curl http://localhost:8001/cooperativas
curl http://localhost:8000/metrics
```

## Monitorización (Prometheus + Grafana)

El `docker-compose.hetzner.yml` incluye **prometheus** (9090) y **grafana** (3000).

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (user: `admin`, pass: `admin`)

**Configurar dashboard en Grafana:**

1. Añadir data source: **Prometheus** → URL `http://prometheus:9090`
2. Importar dashboard: **"Docker and System Monitoring"** (ID: 10600)

Configuración de Prometheus en `docker/prometheus.yml`. Cambiar `.env` a valores de producción y repetir despliegue.

**Automatización con ArgoCD:** despliegue continuo en Kubernetes (k3s en Hetzner), sincronización desde Git, Prometheus/Grafana y GitHub Actions. Ver [ArgoCD (automatización)](argocd-automation.md).

Documentación completa: [Hetzner.md](../deploy/Hetzner.md).
