# Checklist — integraciones y mejoras (2026)

*Estado: ✅ / 🟡 / ⬜ / 📋 — [Ver análisis detallado](./PRONTUARIO-ANALISIS-CURSOR-INTEGRACIONES-2026.md).*

**Versión:** 2026-03-24 · **Orden:** P1 crítico → P2 importante → P3 futuro.  
**Límite:** estados según **evidencia en el clon**; sin SLA contractual, sin nombres propios, sin “valor actual” de rendimiento sin medición archivada.

**Relación:** [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) · [PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md](./PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md) · [PRONTUARIO-ANALISIS-CURSOR-INTEGRACIONES-2026.md](./PRONTUARIO-ANALISIS-CURSOR-INTEGRACIONES-2026.md) · [ROADMAP-MEJORAS-P1-P5-2026.md](./ROADMAP-MEJORAS-P1-P5-2026.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) · [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md) · [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) · [DPIA-TraceChain-2026.md](../legal/DPIA-TraceChain-2026.md)

### Leyenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Implementado y comprobable en repo (tests o artefacto) |
| 🟡 | Parcial (ej. `/metrics` sí, Grafana no versionada) |
| ⬜ | Pendiente |
| 📋 | Stub / documentación / I+D físico sin cierre en código |

---

## 1. Computación neuromórfica (SNN) + Redis

| Tarea | P | Estado | Dependencias | Enlaces | Notas |
|-------|---|--------|--------------|---------|--------|
| Caché SNN (`hydro_infer_dict`) | P1 | 🟡 | `redis>=5.0.0`, `CASTUO_SNN_CACHE_REDIS_URL` | [robotics README](../../backend/integrations/robotics/README.md) | `neuromorphic_edge.py`; sin clase `MemristorCache` dedicada |
| `test_snn_cache_hit_reproducible` | P1 | ✅ | pytest | [test_neuromorphic_redis_cache.py](../../tests/integrations/test_neuromorphic_redis_cache.py) | — |
| `test_snn_cache_ttl_expiry` | P1 | ✅ | pytest | Mismo fichero | `_FakeRedisTTL` |
| TTL por env + estación (`snn_cache_ttl_seconds`) | P2 | 🟡 | — | [robotics README](../../backend/integrations/robotics/README.md) | `CASTUO_SNN_CACHE_TTL_SECONDS` o `CASTUO_SNN_CACHE_SEASON` |
| Métricas Prometheus | P1 | 🟡 | `prometheus_client` | [lab_metrics_optional.py](../../backend/integrations/robotics/lab_metrics_optional.py) | `GET /metrics` en lab (**8011** / **8012**, no 8000 por defecto); Grafana ⬜ |
| Logs JSON estructurados | P2 | ⬜ | — | — | Lab: `logging` estándar |

---

## 2. Señales y memristores

| Tarea | P | Estado | Dependencias | Enlaces | Notas |
|-------|---|--------|--------------|---------|--------|
| GNU Radio / RF | P2 | 🟡 | GNU Radio stack | [GNU_RADIO.md](../../backend/integrations/robotics/GNU_RADIO.md) | Agrovoltaica: [spin-offs/agrovoltaic-eu/README.md](../../spin-offs/agrovoltaic-eu/README.md) (no sustituye guía RF) |
| Prototipo Nb₂O₅ / hardware | P3 | 📋 | Laboratorio | [ROADMAP-TRL6-TRL7-CODE.md](./ROADMAP-TRL6-TRL7-CODE.md) | Fuera del pytest |
| Cifrado Kyber / PQC | P2 | 🟡 | `pqcrypto` opcional | [pq_crypto.py](../../backend/security/pq_crypto.py) | No está en `backend/utils/` |
| VO₂ / simulación | P3 | 📋 | — | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) si aplica sensores | Humedad agregada ≠ DPIA TraceChain por sí sola |

---

## 3. Trazabilidad (TraceChain)

| Tarea | P | Estado | Dependencias | Enlaces | Notas |
|-------|---|--------|--------------|---------|--------|
| Persistencia stub PEI-002 (SQLite) | P1 | 🟡 | sqlite3 | [`sqlite_store.py`](../../pei-002-tracechain/api/sqlite_store.py) | Tablas `sigpac_validation_envelopes`, `parcel_validations`; migración desde `envelopes`/`parcels` si existían. **🟡** hasta smoke Docker + volumen ([`tests/smoke/smoke_test_persistence.sh`](../../tests/smoke/smoke_test_persistence.sh)) |
| Stub PEI-002 `/api/pei-002/envelope` | P1 | ✅ | — | [pei-002-tracechain/README.md](../../pei-002-tracechain/README.md) | Puerto **8010**; contrato Pydantic sin cambios |
| Cadena Gaia (servicio) | P2 | 🟡 | RPC + clave | [gaia_chain.py](../../backend/services/gaia_chain.py), [TraceChain-Compliance-2026.md](../legal/TraceChain-Compliance-2026.md) | Nodo/contrato reales ⬜ política |
| DPIA robotics + §6 cadena lab | P1 | 🟡 | DPO | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) | Documento ✅; **firma / ampliación memristores** ⬜ |
| `parcel_id` en payloads / on-chain | P2 | 🟡 | — | Snapshot lab con `parcel_id`; minimización §6 | `register_sigpac_digest.py` según flujo PEI |

---

## 4. Monitorización y alertas

| Tarea | P | Estado | Dependencias | Enlaces | Notas |
|-------|---|--------|--------------|---------|--------|
| Grafana | P2 | ⬜ | prometheus, grafana | [alerts.md](../monitoring/alerts.md) | Dashboards fuera del git |
| Métrica `castuo_neuro_memristor_latency_ms` | P3 | ⬜ | — | — | No definida en código |
| Alertas latencia / cadena | P2 | 🟡 | — | [alerts.md](../monitoring/alerts.md) | PromQL orientativo; webhooks fuera del git |
| Estrés Locust | P2 | 🟡 | `locust` | [tests/stress/README.md](../../tests/stress/README.md), [locustfile.py](../../tests/stress/locustfile.py) | Medir baseline sin fijar meta en md |

---

## 5. Integración con sistemas existentes

| Tarea | P | Estado | Enlaces | Notas |
|-------|---|--------|---------|--------|
| SNN ↔ SIGPAC / usos | P2 | 🟡 | [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md), [PLAN-EXCELENCIA-V2.5-REFUERZO.md](../legal/PLAN-EXCELENCIA-V2.5-REFUERZO.md) | PEI-001 |
| Formación agrovoltaica | P3 | 📋 | [spin-offs/agrovoltaic-eu/README.md](../../spin-offs/agrovoltaic-eu/README.md) | — |
| TraceChain ↔ parcela | P2 | 🟡 | [TraceChain-Compliance-2026.md](../legal/TraceChain-Compliance-2026.md) | `/api/pei-002/parcel` |
| Scrape Prometheus ↔ Grafana | P1 | 🟡 | [robotics README](../../backend/integrations/robotics/README.md) | Solo exposición `/metrics` en app |

---

## 6. Documentación pendiente / seguimiento

| Documento | Sección | Estado | Enlaces |
|-----------|---------|--------|---------|
| DPIA-Robotics-2026 | Memristores / SNN ampliado | 🟡 | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |
| robotics README | GNU Radio (enlace explícito arriba) | 🟡 | `GNU_RADIO.md` |
| tests/stress | Locust | 🟡 | README + `locustfile.py` |

---

## 7. Enlaces relacionados

- [ROADMAP-MEJORAS-P1-P5-2026.md](./ROADMAP-MEJORAS-P1-P5-2026.md)
- [PLAN-EXCELENCIA-V2.5-REFUERZO.md](../legal/PLAN-EXCELENCIA-V2.5-REFUERZO.md)
- [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md)
- [system_admin_playbook.py](../../backend/models/system_admin_playbook.py) (governance; incluye `critical_hardening_checks` / Multilinker)
- [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) (red LLMNR + capa operativa Multilinker)

---

## 8. Plan corto (sin responsables)

| Ventana | Acciones |
|---------|----------|
| Corto | Scrape `/metrics` en staging; revisar TTL con `CASTUO_SNN_CACHE_SEASON` + métricas hit/miss |
| Medio | Ejecutar Locust y archivar resultados; RF bajo DPIA |
| Largo | Hardware memristor con informe externo; nodo Gaia según contrato |

---

## 9. Métricas globales (plantilla — rellenar tras medición)

| Objetivo | Fuente | Valor | Meta interna |
|----------|--------|-------|----------------|
| Latencia inferencia | `castuo_neuro_hydro_infer_seconds` | *medir* | *acordar* |
| Throughput | Locust + Redis | *medir* | *acordar* |
| On-chain | Logs / explorer | *medir* | *acordar* |

---

*Quien fija cifras de rendimiento en markdown sin export de benchmark desconecta el manómetro del depósito.*
