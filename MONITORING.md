# CASTUO-SYSTEM™ — Monitoring Enterprise v5.2

Stack de observabilidad para producción (Hetzner CAX21): métricas API, IoT, blockchain, drones y alertas.

---

## Accesos rápidos (v5.2)

| Servicio     | URL / Puerto       | Credenciales        |
|--------------|--------------------|----------------------|
| Landing      | `:3000`            | —                    |
| Grafana      | `:3001`            | admin / castuo123    |
| Prometheus   | `:9090/targets`    | —                    |
| Alertmanager | `:9093`            | —                    |

## Checklist post-deploy (5 min)

1. Verificar **castuo-api** en Prometheus (`UP`).
2. Importar dashboards Grafana (IDs: **1860**, **14998**, **13650**, **18864**).
3. Probar alerta simulada:
   ```bash
   curl -X POST http://localhost:9093/api/v2/alerts -H "Content-Type: application/json" -d '[{"labels": {"alertname": "Test", "severity": "critical"}}]'
   ```
4. Revisar logs de blockchain (si aplica): `docker logs castuo-blockchain 2>/dev/null | grep "GS1 EPCIS"`.

## Dashboards obligatorios (Grafana)

| Dashboard           | ID Grafana | Métricas clave                          | Umbral crítico              |
|---------------------|------------|-----------------------------------------|-----------------------------|
| FastAPI Performance | 1860       | castuo_api_calls_total, request_duration| Latencia > 500ms → Alerta   |
| IoT Sensors         | 14998      | Temp, humedad, luz, suelo               | Temp > 35°C → Emergency Stop|
| Blockchain          | 13650      | GS1 EPCIS, BioCoin minados               | Fallo TX → Notificación legal |
| Drones Castuo Link  | 18864      | Batería, cobertura antenas, misiones    | Batería < 20% → Ruta estación |

## Alertas críticas (configurar ya)

- **IoT**: Temp > 35°C → Emergency Stop.
- **API**: Latencia > 500ms → Notificar a #alertas-castu.
- **Blockchain**: Fallo en TX → Legal review + SMS.

Alertmanager (v5.2) está configurado con `admin-team` (email + Slack). Ver `monitor/alertmanager.yml` y sustituir `api_url` y `to` por valores reales.

---

## 1. Stack

- **Prometheus**: scraping de la API (`/metrics`) y n8n.
- **Grafana**: dashboards y alertas (puerto 3001 para no colisionar con el frontend en 3000).

## 2. Despliegue (3 comandos)

Ejecutar desde la raíz del proyecto (mismo directorio = misma red Docker para que Prometheus alcance `api:8000` y `n8n:5678`):

```bash
cd /castuo-ctaex

# 1. Backend con métricas
docker-compose up -d --build api

# 2. Monitoring stack (Prometheus + Grafana + Alertmanager)
docker-compose -f docker-compose.monitor.yml up -d

# 3. Verificar targets
curl -s http://localhost:9090/api/v1/targets | head -20
```

**Accesos:**

| Servicio     | URL (producción)              | Credenciales   |
|-------------|--------------------------------|----------------|
| Prometheus  | https://89.167.5.233:9090      | —              |
| Grafana     | https://89.167.5.233:3001      | admin / castuo123 |
| Alertmanager| https://89.167.5.233:9093      | —              |

**Checklist post-deploy (5 min):**

| Servicio        | URL / Puerto   | Estado esperado        |
|-----------------|----------------|------------------------|
| Landing         | :3000          | Dashboard v5.0         |
| Grafana         | :3001          | admin / castuo123      |
| Prometheus      | :9090/targets  | castuo-api UP          |
| FastAPI Metrics | api:8000/metrics | castuo_* metrics    |
| Alertmanager    | :9093          | Config loaded          |

## 3. Configuración Prometheus y alertas

- **monitor/prometheus.yml**: scrape de `castuo-api` (api:8000/metrics), `castuo-n8n` (n8n:5678), y envío de alertas a Alertmanager (9093). Incluye `rule_files: alertas.yml`.
- **monitor/alertas.yml**: reglas ApiHighLatency (P95 > 500ms, 2m) y LERBajo (castuo_ler < 1.2, 5m).
- **monitor/alertmanager.yml**: v5.2 — receptor `admin-team` (email + Slack #alertas-castu). Sustituir `api_url` y `to` por valores reales.

## 4. API — Métricas y endpoint de estado

- **GET /metrics**: formato Prometheus (latencia por ruta, contador de llamadas por endpoint y status). Usado por Prometheus para scraping.
- **GET /monitoring/status**: JSON para el widget de la landing (`ler`, `api_uptime_pct`, `efficiency_pct`, `status`). Sin lógica de negocio; solo operativo.

## 5. Primer dashboard Grafana (importar ya)

1. **Grafana** → http://localhost:3001 (o https://89.167.5.233:3001) → Login: admin / castuo123.
2. **Add datasource** → Prometheus → URL: `http://prometheus:9090` → Save & Test.
3. **Import dashboards**: Dashboards → Import → ID **1860** (FastAPI) y/o **14998** (CASTUO custom si existe).
4. **Comprobar métricas en vivo**:
   - `castuo_api_calls_total{endpoint="/hidroponia/sensors"}`
   - `castuo_request_duration_seconds` (P95)
   - `castuo_ler` = 1.54

## 6. Dashboards Grafana (recomendados)

1. **API Performance**
   - Request duration P95 (alerta si supera umbral alto).
   - Error rate (HTTP 5xx).
   - Llamadas por minuto por endpoint (Hidroponía, Agrovoltaica, Dronica).

2. **Usuarios**
   - Usuarios activos (si se expone métrica).
   - Tasa login/registro y duración de sesión (cuando existan).

3. **Sistema**
   - CPU/RAM del servidor (node exporter si se añade).
   - Estado de contenedores.
   - Uptime HTTPS.

4. **ROI Agrovoltaica**
   - LER (alerta si baja de umbral).
   - Eficiencia (%).
   - kWh hoy vs ayer (cuando exista fuente de datos).

## 6. Alertas críticas sugeridas

- **Latencia P95 > umbral** → Crítico.
- **Error rate > 5%** → Crítico.
- **LER < umbral** → Aviso (impacto ROI).
- **CPU > 90%** → Aviso.
- **HTTPS down** → Crítico.

Notificaciones: configurar en Grafana (Slack, email).

## 8. Integración en la landing v5.0

El **index.html** (y CASTUO-SYSTEM-v5.0.html) incluye un bloque que llama a `/api/monitoring/status` cada 30 s y muestra:
- API Status (uptime %).
- LER actual (con color según umbral).

## 9. Deploy + test (3 comandos, listo CTAEX)

```bash
cd /castuo-ctaex

# 1. Backend con métricas (ya instrumentado)
docker-compose up -d --build api

# 2. Monitoring stack (Grafana en 3001)
docker-compose -f docker-compose.monitor.yml up -d

# 3. Verificación
curl -s http://localhost:9090/api/v1/targets
```

## 10. Comando 1-click (stack + monitoring)

```bash
cd /castuo-ctaex && \
git pull && \
docker-compose up -d --build api && \
docker-compose -f docker-compose.monitor.yml up -d && \
curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[^"]*"'
```

## 11. Valor técnico

- Observabilidad de nivel producción.
- Alertas proactivas para proteger ROI y disponibilidad.
- Demo CTAEX con monitoring en vivo.
- Base para cumplimiento y escalado posterior.
