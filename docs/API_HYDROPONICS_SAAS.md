# API Hidroponía SaaS (CASTUO-SYSTEM)

Este módulo persiste evidencia de hidroponía en PostgreSQL y ancla eventos en GaiaChain (si configurado).

## Autenticacion

Incluye header `X-API-KEY`.

- Claves permitidas: `HYDROPONICS_SAAS_API_KEYS` (coma-separadas) o `N8N_API_KEY`.
- Fallback dev (si no hay env): `default_n8n_key_123`.

## Endpoints

### 1) Guardar lecturas de sensores

`POST /hydroponics-saas/sensor-readings`

Body JSON:

```json
{
  "sensor_id": "ph_1",
  "sensor_type": "ph",
  "value": 6.8,
  "location": "greenhouse_1",
  "unit": "pH",
  "zone_id": "zone_cannabis_1"
}
```

Ejemplo `curl`:

```bash
curl -X POST "http://localhost:8000/hydroponics-saas/sensor-readings" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: default_n8n_key_123" \
  -d '{
    "sensor_id": "ph_1",
    "sensor_type": "ph",
    "value": 6.8,
    "location": "greenhouse_1",
    "unit": "pH",
    "zone_id": "zone_cannabis_1"
  }'
```

### 2) Guardar análisis diario

`POST /hydroponics-saas/daily-analysis`

Body JSON:

```json
{
  "zone_id": "zone_cannabis_1",
  "overall_status": "optimal",
  "issues": [{"type": "high_temperature", "value": 28.5}],
  "recommendations": ["increase ventilation"],
  "trends": [{"type": "ph_stable", "value": 6.8}],
  "priority": "medium"
}
```

Ejemplo:

```bash
curl -X POST "http://localhost:8000/hydroponics-saas/daily-analysis" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: default_n8n_key_123" \
  -d '{
    "zone_id": "zone_cannabis_1",
    "overall_status": "optimal",
    "issues": [{"type": "high_temperature", "value": 28.5}],
    "recommendations": ["increase ventilation"],
    "trends": [{"type": "ph_stable", "value": 6.8}],
    "priority": "medium"
  }'
```

### 3) Históricos de sensores

`GET /hydroponics-saas/history/sensor-readings?zone_id=...&days=7&sensor_type=ph`

Ejemplo:

```bash
curl "http://localhost:8000/hydroponics-saas/history/sensor-readings?zone_id=zone_cannabis_1&days=7&sensor_type=ph" \
  -H "X-API-KEY: default_n8n_key_123"
```

### 4) Históricos de análisis diarios

`GET /hydroponics-saas/history/daily-analysis?zone_id=...&days=30`

Ejemplo:

```bash
curl "http://localhost:8000/hydroponics-saas/history/daily-analysis?zone_id=zone_cannabis_1&days=30" \
  -H "X-API-KEY: default_n8n_key_123"
```

### 5) Guardar cultivos (hidropónico genérico)

`POST /hydroponics-saas/crops`

Body JSON:

```json
{
  "crop_id": "crop_001",
  "zone_id": "zone_cannabis_1",
  "plant_type": "lettuce",
  "planting_date": "2026-04-01T12:00:00",
  "growth_stage": "vegetative",
  "quantity": 100,
  "status": "active",
  "metadata": { "source": "n8n" }
}
```

### 6) Registrar cosecha

`PUT /hydroponics-saas/crops/{crop_id}/harvest`

Body JSON:

```json
{
  "harvest_date": "2026-04-10T12:00:00",
  "weight": 123.4,
  "quality": "optimal",
  "notes": "Cosecha exitosa",
  "zone_id": "zone_cannabis_1"
}
```

### 7) Históricos de cultivos

`GET /hydroponics-saas/history/crops?zone_id=...&days=30`

### 8) Históricos de cosechas

`GET /hydroponics-saas/history/harvests?zone_id=...&days=365`

## Metrics Prometheus

- `hydroponics_saas_readings_total{sensor_type="ph"}`
- `hydroponics_saas_analysis_total{status="optimal|..."}`

Reglas en `prometheus/alert.rules.yml`.

