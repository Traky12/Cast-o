# Roadmap mejoras P1–P5 (performance, observabilidad, seguridad, campo, comercial)

**Versión:** 2026-03-23 · **Orientativo:** priorización técnica. **Prohibido** interpretar este markdown como valoración de empresa, ROI certificado o compromiso de plazos contractuales.

**Relación:** [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) (matriz P1–P3 ejecutiva) · [ROADMAP-TRL6-TRL7-CODE.md](./ROADMAP-TRL6-TRL7-CODE.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) · [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md) (concepto I+D vs simulación git)

---

## P1 — Performance y colas (Q1 orientativo)

| Mejora | Estado repo | Riesgo / nota |
|--------|-------------|---------------|
| Caché Redis opcional SNN | `CASTUO_SNN_CACHE_REDIS_URL` + TTL; inferencia **determinista por semilla** cuando caché activa (coherencia hit/miss) | Sin Redis, comportamiento anterior (Poisson global) |
| Workers asíncronos (Celery/RQ) | **Diseño**; cadena y sellado requieren idempotencia y política DPO | No forzar `background_tasks` en TX sin colas duras en edge |
| Métricas Prometheus opcionales | `CASTUO_PROMETHEUS_METRICS=1` + `prometheus_client` | Solo lab stub hasta integrar en monolito con acuerdo |

**Código inmediato implementado:** caché SNN + `/metrics` opt-in (ver `neuromorphic_edge`, `lab_metrics_optional`).

### Tests TRL6 (`tests/integrations/test_neuromorphic_redis_cache.py`)

| Test | Comportamiento verificado |
|------|---------------------------|
| `test_snn_cache_hit_reproducible` | Mismos sensores → mismo `riego_ml` y `chain_seal` en el segundo hit |
| `test_snn_cache_ttl_expiry` | Tras avanzar el reloj simulado > TTL, `setex` se vuelve a ejecutar (miss) |

### Hipótesis de escalado (ilustrativo — **no** medido en este repositorio)

Cifras tipo “50 req/s vs 350 req/s”, “7× throughput” o “ha/s” son **objetivos de diseño** hasta benchmark en staging con Redis real, latencia de red y tamaño de payload. No usarlas como evidencia contractual ni en informe TRL6 sin trazas Prometheus.

---

## P2 — Observabilidad producción (Q1–Q2)

| Mejora | Dirección |
|--------|-----------|
| Grafana | Scraping de `/metrics` ya expuesto en lab; stack Grafana fuera del git |
| Logs JSON | `structlog` + `trace_id` en gateway; no PII en parcela sin DPIA |
| Alertas | `chain_registration=failed` vía reglas Prometheus/Loki — umbral acordado con operación |

---

## P3 — Postura seguridad (Q2)

| Mejora | Dirección |
|--------|-----------|
| Rate limit por Bearer | Middleware FastAPI o reverse proxy (Caddy/Traefik) |
| WAF / firewall | Hetzner Cloud Firewall + reglas geográficas si aplica |
| HSM / Vault Transit | `GAIA_CHAIN_PRIVATE_KEY` y `ADMIN_MASTER_KEY` según [VAULT_KV_PATHS.md](../../backend/security/VAULT_KV_PATHS.md) |
| Rotación Bearer | Política 90d documentada; fuera del código hasta `auth_roles` evolutivo |

---

## P4 — TRL7 campo (Q2)

| Mejora | Dirección |
|--------|-----------|
| MQTT → SNN | Broker (p. ej. EMQX); contrato topic + esquema JSON; DPIA si hay ubicación |
| Sensores reales | Calibración agronómica; A/B manual vs `riego_ml` **medido**, no solo sim |
| Hardware | Especificación por RFQ; sin anclar marca en obligación legal del repo |

---

## P5 — Comercialización (Q3)

| Mejora | Dirección |
|--------|-----------|
| Multi-tenant | `tenant_id` separado de `parcel_id`; RBAC extendido |
| Billing | Stripe/Paddle bajo DPA; fuera del lab stub |
| PWA móvil | Offline-first implica política de retención local RGPD |

---

## Esfuerzo relativo (persona-días — **indicativo**)

| Prioridad | Bloque | Orden magnitud |
|-----------|--------|-----------------|
| P1 | Redis + métricas + diseño colas | 3–8 d |
| P2 | Grafana + logs estructurados | 3–10 d |
| P3 | Rate limit + Vault/HSM operativo | 7–20 d |
| P4 | MQTT + campo | 10–30 d |
| P5 | Multi-tenant + billing | 15–40 d |

---

*Escalar hectáreas sin medir litros reales es simular cosecha en PowerPoint.*
