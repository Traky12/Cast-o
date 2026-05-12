# Alertas — Prometheus / Grafana (orientativo)

**Versión:** 2026-03-24 · **Ámbito:** lab robotics (`castuo_neuro_*`), health, cadena opt-in.  
**Límite:** no hay `alertmanager.yml` ni dashboards en el repo. Webhooks (Slack, Teams, PagerDuty) = **secretos** y configuración en tu entorno.

---

## 1. Fuentes de datos

| Fuente | Condición |
|--------|-----------|
| `GET /metrics` (lab) | `CASTUO_PROMETHEUS_METRICS=1` + `prometheus_client` |
| `GET /health` | Sin Bearer; `chain_status`, `neuromorphic_lab` |
| Redis | Solo si despliegas **redis_exporter** u otro scrape aparte del lab |

---

## 2. Tabla de alertas (ejemplos PromQL — ajustar umbrales tras baseline)

| Alerta | Consulta (ejemplo) | Umbral típico | Severidad | Notas |
|--------|-------------------|---------------|-----------|--------|
| Latencia p95 inferencia | `histogram_quantile(0.95, sum(rate(castuo_neuro_hydro_infer_seconds_bucket[5m])) by (le))` | > *s* acordado | warning | Sustituir `0.05` por segundo real medido |
| Bajo tráfico inesperado | `rate(castuo_neuro_hydro_infer_seconds_count[5m])` | < *req/s* mínimo | warning | Solo si tienes tráfico esperado continuo |
| Redis down (exporter) | `redis_up == 0` | — | critical | **Requiere** redis_exporter en Prometheus; no viene del lab |
| Errores HTTP stub | `sum(rate(http_requests_total{status=~"5.."}[5m]))` | > 0 | critical | Requiere instrumentación HTTP compatible o logs |

**Cadena:** hoy no hay `chain_failed_total` en métricas; usar logs estructurados o reglas sobre `chain_registration` en logs.

---

## 3. Buenas prácticas

1. **Labels:** no poner `parcel_id`, token ni PII en series Prometheus.  
2. **Silencios:** usar ventanas de mantenimiento en Alertmanager.  
3. **Runbook:** cada alerta con contexto, acción inicial y escalado (documento interno, no en git con URLs reales).  
4. **RGPD:** si la alerta implica datos personales o parcela identificable, coordinar con DPO.

---

## 4. Ejemplo esquemático Alertmanager (sin secretos)

```yaml
# reference-only — no commitear tokens
route:
  receiver: default
receivers:
  - name: default
    # webhook_configs: - url_file: /run/secrets/alert_webhook_url
```

---

*La alarma que dispara sin runbook es estrés hidráulico mal gestionado.*
