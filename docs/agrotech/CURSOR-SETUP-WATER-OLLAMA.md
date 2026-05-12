# Configuración inicial en Cursor — agua CTAEX + Ollama Cloud

Este repositorio ya implementa el análisis en `backend/routers/water_ctaex.py` con **Ollama Cloud vía `httpx`** (`POST …/chat/completions`, API compatible OpenAI). **No** sustituyas ese router por el paquete Python `ollama` ni por `from ollama import Client` salvo decisión explícita del equipo.

## 1. Abrir el proyecto y sincronizar

Abre la carpeta raíz de Castúo-System en Cursor y sincroniza con Git (`git pull` / merge) antes de editar `.env`.

## 2. Variables de entorno

1. Copia `.env.example` → `.env` (si aún no existe).
2. Añade o edita **sin pegar claves de ejemplo en repositorios públicos**:

```bash
OLLAMA_API_KEY=<tu_clave_real>
OLLAMA_BASE_URL=https://api.ollama.com/v1
OLLAMA_MODEL=llama3.2:3b
# LANGSMITH_API_KEY=   # opcional
```

3. Guarda el archivo localmente; confirma que `.env` está en `.gitignore`.

## 3. Docker Compose

En la raíz, el servicio del backend FastAPI se llama **`api`** (no `castuo-api`). Verifica en `docker-compose.yml` que `environment` incluye `OLLAMA_API_KEY`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` y, si aplica, `LANGSMITH_API_KEY` para `api` y las variables Ollama necesarias para `n8n`.

## 4. Dependencias Python

El backend **no** requiere `pip install ollama`; la dependencia usada es **`httpx`** (ya en `backend/requirements.txt`). Solo instala `ollama` si otro script lo importa explícitamente.

## 5. Workflow n8n

No reemplaces `n8n/workflows/castuo_n8n_water_mqtt_analysis.json` por plantillas con topics múltiples obsoletos o nodos Slack incorrectos. El flujo versionado usa MQTT `castuo/water/sensor/+`, Code v2, HTTP Request con timeout largo para IA, y webhook Slack opcional.

Si activas **cuotas SaaS** (`WATER_CTAEX_ENFORCE_QUOTA=1`), el nodo HTTP debe enviar **`X-API-KEY`** con una clave presente en `WATER_API_KEY_TO_PLAN` (JSON). Sin cuota (por defecto), no hace falta cambiar el workflow.

## 6. Reinicio y prueba

```bash
docker compose down && docker compose up -d
```

```bash
curl -s -X POST "http://127.0.0.1:8000/water/ctaex/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"sensor_type\":\"orp\",\"sensor_value\":580,\"historical_data\":[{\"sensor_value\":650,\"timestamp\":\"2026-03-28T10:00:00Z\"}]}"
```

Comprueba `ollama_analysis` en el JSON y `GET /water/ctaex/health` (`version` **1.3**, `ollama_configured`, `water_quota_enforcement`).

## 7. Documentación

Detalle de API y límites: [WATER-SYSTEM-CTAEX.md](./WATER-SYSTEM-CTAEX.md).

## 8. Stripe (opcional)

Define en `.env` `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` y `FRONTEND_URL`. El checkout reutilizable del repo es **`POST /ecommerce/create-checkout`** (CTAEX, no `/subscriptions/checkout-session`). Tras el pago, asigna claves en `WATER_API_KEY_TO_PLAN` o amplía webhooks según vuestra pasarela.
