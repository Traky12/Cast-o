# Prontuario maestro — evaluación técnica CASTÚO-System (2026)

*Evaluación **honesta** del estado de desarrollo para equipos (p. ej. Cursor): solo afirmaciones **ancladas al repositorio** o marcadas como *despliegue externo*. Los **TRL** etiquetan **madurez del artefacto en git**, no certificación de campo. Revisar tras cada release mayor.*

**Relación:** [PLAN-MEJORA-INMEDIATA-CASTUO-2026.md](./PLAN-MEJORA-INMEDIATA-CASTUO-2026.md) (táctico) · [PRONTUARIO-PLAN-FASES-ESTABILIZACION-20S-2026.md](./PRONTUARIO-PLAN-FASES-ESTABILIZACION-20S-2026.md) (roadmap 20 semanas) · [PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md](./PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md) · [PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md](./PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md) · [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) · [PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md](./PRONTUARIO-MAESTRO-AUDITORIA-EVOLUCION-RESILIENTE-2026.md) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [backend/integrations/robotics/README.md](../../backend/integrations/robotics/README.md)

---

## 📋 1. Metodología de evaluación

1. Componentes **localizables** (ruta de archivo o test).  
2. **TRL** = progreso del **código/docs** en repo, no aval regulatorio.  
3. **Gaps** formulados para ser **cerrados** con PR, checklist o runbook.  
4. **Trazabilidad:** vulnerabilidad → evidencia → solución → **§ de refuerzo** en este documento.  
5. No se inventan módulos: si no existe `sensor_validation.py`, se indica *diseño pendiente*.

---

## 🔧 2. Estado de componentes principales

| Componente | Estado real | Evidencia en código | Gaps críticos | Prioridad |
|--------------|-------------|---------------------|---------------|-----------|
| **SNN** (`neuromorphic_edge.py`) | **TRL-4 (simulación)** | Docstring: *«Simulador TRL-4: SNN ligera…»*; inferencia en `hydro_infer_dict`; `HydroSensorIn`; `snn_cache_ttl_seconds()`; tests `tests/integrations/test_neuromorphic.py`, `test_neuromorphic_redis_cache.py` | Validación Pydantic **solo** en `/api/robotics/lab/neuromorphic/hydroponics/infer` (`attach_neuromorphic_routes`); riesgo de regresión **TTL/cache** si cambia env Redis o estación | 🔥🔥 |
| **GaiaChain (lab)** | **Opt-in** (no es prod por defecto) | `backend/integrations/robotics/lab_gaiachain_optional.py` → `try_register_lab_audit_event` → `register_event_in_chain`; sellado PQC opcional en salida SNN (`chain_seal` vía `pq_crypto`) | Sin **tx on-chain** si faltan `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER`, contrato, ABI o clave; no sustituye nodo/auditoría de red real | 📋 |
| **LocalResilienceDB** | **TRL-5 (SQLite local)** | `backend/database/local_db.py` — cola `pending_operations`, `sqlite3`, sync opcional hacia CLI cadena | **Backup automático** del fichero `resilience.db` no definido en el repo; riesgo de pérdida en host único | 🔥 |
| **SIGPAC / parcela** | **TRL-3 (placeholders + validación manual)** | `sigpac_validator.py` (GeoJSON / anillos / GDAL opcional); `sigpac_remote_placeholder.py`; compliance generator menciona APIs *stub* | Sin integración API regional **real**; mapeo **estático** en docs generados; validación geométrica incompleta sin GDAL | 🔥 |
| **Señales (RF/IoT)** | **TRL-3 (diseño)** | `signal_manager.py` (snapshots cifrados); [GNU_RADIO.md](../../backend/integrations/robotics/GNU_RADIO.md) **stub** documental | Sin **GNU Radio** en runtime del monolito; sin hardware SDR en repo; memristores **solo** metáfora/sim en SNN | 📋 |
| **Infraestructura** | **TRL-4 (staging documentado)** | `docker-compose.staging.yml` (Vault, ZAP, backend, auto-rotate — **un réplica** de app sin balanceador); `docs/deploy/CHECKLIST-TRL6-HETZNER-STAGING.md` | Sin **HA** (réplicas, LB); backup de volúmenes compose **responsabilidad operador**; configuración mínima para CI/CD local | 🔥🔥 |

*Prioridad 🔥 > 📋 es orientativa (riesgo × facilidad de explotación / impacto al negocio agua-dato).*

---

## 📊 3. Vulnerabilidades, impacto y trazabilidad

*Cada fila enlaza a la **solución propuesta** en §4 para auditorías (ticket ↔ sección).*

| Vulnerabilidad / riesgo | Impacto | Evidencia | Solución propuesta |
|-------------------------|---------|-----------|---------------------|
| **LLMNR / mDNS poisoning** | Robo de sesión / relay en LAN mixta | `tcpdump -i any udp port 5355` en hosts sin hardening; playbook `llmnr_multicast_off` | **§4.1** — Deshabilitar LLMNR/mDNS (`systemd-resolved`, GPO Windows); [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) |
| **Validación de sensores** | Decisiones agrícolas incorrectas | Una ruta consolidada con `HydroSensorIn` en `neuromorphic_edge.py` (no hay `routes.py` separado para este lab) | **§4.2** — Extender modelos Pydantic por router; tests de regresión; *módulo dedicado `sensor_validation.py` **no existe** aún — crear o centralizar dependencias FastAPI* |
| **Falta de HA** | Indisponibilidad del servicio | `docker-compose.staging.yml`: un servicio `backend` sin réplicas ni LB | **§4.3** — Balanceo + ≥2 réplicas o orquestador; runbook failover; alineado a [PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md](./PRONTUARIO-MAESTRO-INFRAESTRUCTURA-SOBERANA-TRL6-TRL7-2026.md) |
| **Observabilidad** | Incidentes tardíos, sin SLO medible | `docs/monitoring/alerts.md`; histograma lab en `lab_metrics_optional.py`; **no** hay `docs/monitoring/grafana/` con dashboards versionados obligatorios | **§4.4** — Scrape `/metrics`, dashboards Grafana mínimos, alertas; artefactos opcionales en auditorías bajo `castu-monitoring/` |

---

## 🛡️ 4. Refuerzo operativo *(acciones vinculadas a §3)*

### 4.1 LLMNR / mDNS

- Aplicar remedición del playbook: `CRITICAL_HARDENING_CHECKS` → `system_admin_playbook.py`.  
- Evidencia: salida de `grep`/`resolvectl` y captura `tcpdump` en ventana acordada.  
- No usar `tee -a` ciego en `resolved.conf` — ver [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md).

### 4.2 Validación de sensores

- Inventariar **todas** las rutas `POST`/`PUT` que acepten telemetría.  
- Reutilizar patrón `HydroSensorIn` o capa común en `backend/middleware/` *(crear si no existe)*.  
- Añadir tests que fallen si se omite validación en nuevas rutas.

### 4.3 Alta disponibilidad y backup

- **HA:** segundo nodo o servicio gestionado; healthchecks; LB TLS.  
- **Backup:** `resilience.db`, volúmenes Vault/staging, snapshots DB — [POLITICA-ROTACION-CLAVES.md](./POLITICA-ROTACION-CLAVES.md) + [CHECKLIST-CIFRADO-TOTAL.md](./CHECKLIST-CIFRADO-TOTAL.md).  
- Prueba de **restauración** documentada (fecha, actor).

### 4.4 Observabilidad (Grafana / alertas)

- Exportar dashboards JSON en repo *(p. ej. `docs/monitoring/grafana/`)* o submódulo `castu-monitoring`.  
- Alertas mínimas: errores 5xx, latencia p95 inferencia, certificados < N días.  
- Ver [docs/monitoring/alerts.md](../monitoring/alerts.md).

---

## 🔐 5. Seguridad adicional *(repo vs despliegue)*

| Medida | Estado | Detalles |
|--------|--------|----------|
| Bearer / secretos | Código + docs | `*_FILE`, Vault KV — [VAULT_KV_PATHS.md](../../backend/security/VAULT_KV_PATHS.md) |
| PQC sellado lab | Código | `pq_crypto.py` + metadatos SNN |
| TLS / VPN | Documentación | [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md) |
| MFA / SIEM | Despliegue | IdP, ELK/OpenSearch — roadmap |

---

## 🔄 6. Métricas y rutas de código

| Métrica | Fuente / tipo | Ruta de código o nota |
|---------|---------------|------------------------|
| `castuo_neuro_hydro_infer_seconds` | Prometheus `Histogram` *(lab)* | `backend/integrations/robotics/lab_metrics_optional.py` (`record_neuro_infer_seconds`) |
| **Uptime / carga API** | *No hay `system_metrics.py`* | `backend/main.py`: gauges diversos + Instrumentator; endpoint operativo con `api_uptime_pct` **ilustrativo** en JSON — **no** sustituye métrica de proceso Prometheus `system_uptime` |
| **RPS / carga** | Locust | `tests/stress/locustfile.py` (`RoboticsLabNeuroUser` → infer hidropónica) |
| **Errores de validación** | Logs / futuro contador | *Hoy:* respuestas **422** de FastAPI en logs; *diseño:* middleware central o `sensor_validation` **pendiente** — no afirmar módulo existente |

---

## 📜 7. Documentación y recursos

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| Evolución del sistema | Plan basado en evidencia | [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) |
| Auditoría técnica y ética | Debilidades y roadmap | [PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md](./PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md) |
| Checklist integraciones | Seguimiento P1–P3 | [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) |
| GNU Radio (stub RF) | Integración futura RF/IoT | [GNU_RADIO.md](../../backend/integrations/robotics/GNU_RADIO.md) |
| Cifrado soberano | Staging TLS, secretos | [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md) |

---

## 🎯 8. Conclusión y recomendaciones

### 8.1 Síntesis

- **SNN** es **simulador TRL-4** con tests; el salto a campo exige sensores y validación transversal.  
- **GaiaChain** lab = **opt-in**; el sellado PQC en JSON **no** implica transacción registrada sin config.  
- **SQLite** de resiliencia es **útil** pero **frágil** sin backup de fichero.  
- **SIGPAC** en repo = validación **manual/stub**, no producto SIGPAC integrado.  
- **Staging compose** mejora reproducibilidad pero **no** es HA.

### 8.2 Top 5 acciones

1. Cerrar **§4.1** (LLMNR) en edge operador.  
2. Ejecutar **§4.3** (backup `resilience.db` + prueba restauración).  
3. Implementar **§4.2** (inventario rutas + capa validación).  
4. Desplegar **§4.4** (dashboards + alertas mínimas).  
5. Roadmap **SIGPAC** real o flujo manual auditado.

### 8.3 Estrategia

- Trazabilidad: cada gap con **ticket** que cite **§4.x**.  
- Revisar esta matriz al tocar `neuromorphic_edge.py`, `local_db.py`, `lab_gaiachain_optional.py`, `docker-compose.staging.yml`.

---

*Evaluación que no cita ruta de archivo es opinión; la que cita ruta es territorio auditable.*

*Última revisión estructural: 2026-03 — corregir TRL si cambia el docstring o los tests obligatorios.*
