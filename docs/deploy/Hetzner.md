# Despliegue en Hetzner (CAPA 2 — FastAPI Infra)

Producción con **api-jeremie** (Mistral + JEREMIE) en puerto **8000** y **backend** (Cooperativas + CTAEX) en **8001**.

---

## Build & Deploy

Desde la raíz del repositorio:

```bash
docker-compose -f docker-compose.hetzner.yml up -d --build
```

Servicios:

| Servicio      | Puerto | Descripción                    |
|---------------|--------|--------------------------------|
| api-jeremie   | 8000   | Mistral Adapter, /health, /metrics, JEREMIE |
| backend       | 8001   | /cooperativas, /pac2040/eligibilidad, CTAEX |
| nginx         | 80/443 | Frontend estático + proxy      |

---

## Variables de entorno obligatorias (producción)

Definir en `.env` o en el entorno del host:

| Variable | Uso |
|----------|-----|
| `MISTRAL_API_KEY` | API Key Mistral (api-jeremie) |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL (api-jeremie si usa BD) |
| `API_TOKEN` | Token Bearer para /health y /audit (api-jeremie) |
| `ENVIRONMENT` | `production` para exigir secrets |

Opcionales: `GAIA_CHAIN_API_URL`, `POSTGRES_HOST`, `METRICS_GAIA_TRACES`, `METRICS_COOPERATIVAS_ACTIVAS`, `METRICS_TOTAL_KWP`, `METRICS_PAC2040_FUNDING`.

---

## Healthcheck

- **api-jeremie:** `curl -f http://localhost:8000/mistral/health` cada 30s.
- Si falla 3 veces consecutivas, el contenedor se reinicia.

---

## Validación rápida

```bash
# Mistral Adapter
curl http://localhost:8000/mistral/health

# Cooperativas (backend)
curl http://localhost:8001/cooperativas
curl http://localhost:8001/pac2040/eligibilidad

# Métricas agregadas (api-jeremie)
curl http://localhost:8000/metrics
```

En servidor remoto (Hetzner), sustituir `localhost` por la IP o el host correspondiente.

---

Ver también:

- [Guía avanzada Sabionda Feedback Loop (GDPR/DSA/AI Act)](Hetzner-Avanzado-Sabionda-FeedbackLoop-GDPR-DSA-AIAct.md)
