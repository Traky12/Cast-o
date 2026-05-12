# PRONTUARIO DE ANÁLISIS PARA INTEGRACIONES (2026)

*§6 = RGPD (cumplimiento legal). §9 = ripgrep (`rg`) para búsquedas en código (ej. `rg "setex.*300"`). Sin comandos ficticios de tipo `cursor --search`.*

**Regla de evidencia:** lo marcado como hecho debe comprobarse en el clon (código o tests). Sin SLA de rendimiento sin medición archivada.

**Relación:** [PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md](./PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md) (vista ejecutiva) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) · [NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md)

---

## 1. Debilidades actuales

*Problemas técnicos con impacto en funcionalidad, seguridad o rendimiento.*

### 1.1. SNN + Redis

| Debilidad | Evidencia | Impacto | Prioridad | Código afectado |
|-----------|-----------|---------|-----------|-----------------|
| **Sin clase `MemristorCache`** | Caché acoplada a `hydro_infer_dict` + Redis | Mantenimiento y políticas (TTL, cifrado) dispersas | Media | [`../../backend/integrations/robotics/neuromorphic_edge.py`](../../backend/integrations/robotics/neuromorphic_edge.py) |
| **Validación parcial de sensores** | `POST .../hydroponics/infer` usa `HydroSensorIn` (Pydantic). `neuromorphic_hint_from_metadata` y otros caminos usan `dict` sin el mismo contrato | Riesgo si se amplían rutas sin modelo | Alta | [`../../backend/integrations/robotics/neuromorphic_edge.py`](../../backend/integrations/robotics/neuromorphic_edge.py), [`../../backend/integrations/robotics/lab_stub_app.py`](../../backend/integrations/robotics/lab_stub_app.py) |
| **Sin segunda capa de caché** | Redis ausente o error en `get`/`setex`: inferencia sigue, **sin** LRU/SQLite de respaldo | Latencia y carga en picos | Media | Mismo `neuromorphic_edge.py` |
| **Logs poco estructurados para auditoría de parcela** | No hay convención uniforme `parcela_id` + JSON en todos los módulos | Dificulta trazas forenses | Media | [`../../system_admin_playbook.py`](../../system_admin_playbook.py) y servicios relacionados |

*Nota:* **TTL dinámico** está implementado (`snn_cache_ttl_seconds()`, `CASTUO_SNN_CACHE_TTL_SECONDS`, `CASTUO_SNN_CACHE_SEASON`). No listar como debilidad actual “TTL fijo 300” salvo regresión detectada por auditoría.

### 1.2. TraceChain / PEI-002

| Debilidad | Evidencia | Impacto | Prioridad | Código afectado |
|-----------|-----------|---------|-----------|-----------------|
| **Persistencia del stub** | SQLite vía `PEI002_SQLITE_PATH` o `api/data/pei002_stub.db`. Sin volumen en Docker, el disco del contenedor sigue siendo efímero | Pérdida si se destruye el contenedor sin volumen | Alta (ops) | [`../../pei-002-tracechain/api/main.py`](../../pei-002-tracechain/api/main.py), [`../../pei-002-tracechain/api/sqlite_store.py`](../../pei-002-tracechain/api/sqlite_store.py) |
| **Firma en envelope vs inferencia** | Stub exige `digest` prefijo `sha256:`. El script `register_sigpac_digest.py` no firma Dilithium el envelope hacia el stub; en edge, `seal_inference_payload` usa `dilithium_sign` sobre JSON de inferencia | Modelo de integridad heterogéneo entre piezas | Alta | [`../../pei-002-tracechain/register_sigpac_digest.py`](../../pei-002-tracechain/register_sigpac_digest.py), `neuromorphic_edge.py` |
| **`/parcel` no integrado en flujo SIGPAC vivo** | Endpoint existe; sincronización operativa con SIGPAC productivo no cerrada en repo | Trazabilidad por parcela limitada en lab | Media | [`../../pei-002-tracechain/api/main.py`](../../pei-002-tracechain/api/main.py) |

### 1.3. Señales y memristores

| Debilidad | Evidencia | Impacto | Prioridad | Código afectado |
|-----------|-----------|---------|-----------|-----------------|
| **Sin GNU Radio en runtime** | Documentación stub; sin captura 433 MHz en pipeline | Dependencia de datos simulados / otros buses | Media | [`../../backend/integrations/robotics/GNU_RADIO.md`](../../backend/integrations/robotics/GNU_RADIO.md) |
| **Memristores físicos** | Simulación `HydroponicsSNN` + Redis; sin hardware Nb₂O₅ en software | Latencia “de laboratorio”, no de dispositivo | Baja (I+D) | [`../../docs/integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md`](../integrations/NEUROMORPHIC-MEMRISTOR-ORIENTACION-2026.md) |
| **Cifrado en canal RF** | No hay pipeline Kyber/Dilithium sobre muestras RF | Confidencialidad si se despliega radio en claro | Alta (si RF real) | — |

### 1.4. SIGPAC

| Debilidad | Evidencia | Impacto | Prioridad | Código afectado |
|-----------|-----------|---------|-----------|-----------------|
| **Validador no en todos los flujos** | `sigpac_validator.py` (anillo cerrado, GDAL `IsValid()` cuando aplica) no se invoca automáticamente en cada entrada GeoJSON del ecosistema | Geometrías defectuosas pueden colarse por rutas alternativas | Alta | [`../../backend/integrations/sigpac_validator.py`](../../backend/integrations/sigpac_validator.py) |
| **Mapeo estático** | `mapping.json` sin job de sincronización versionado aquí | Desalineación con SIGPAC si cambian usos | Alta | [`../../pei-001-sigpac/data/mapping.json`](../../pei-001-sigpac/data/mapping.json) |

---

## 2. Puntos críticos

| Punto crítico | Riesgo | Evidencia | Acción inmediata |
|---------------|--------|-----------|------------------|
| **Volumen / backup del SQLite del stub** | Pérdida al recrear contenedor | DB en ruta configurable | Montar volumen o backup de `PEI002_SQLITE_PATH` |
| **Regresión TTL literal `300`** | Caché subóptima | `rg 'setex\\(.*300'` en `neuromorphic_edge.py` | Mantener tests `test_snn_cache_ttl_*` en CI |
| **Rutas nuevas sin Pydantic** | Riego o métricas incoherentes | Extensiones sobre `dict` | Reutilizar o extender `HydroSensorIn` |
| **Integridad TraceChain** | Suplantación / repudio | Solo digest en envelope PEI-002 | Política unificada: `PostQuantumCrypto.dilithium_sign` / verificación donde corresponda |
| **Geometrías por rutas alternativas** | Decisiones territoriales erróneas | Validador no universal | Llamar validador (o Shapely si se unifica stack) en el borde de ingesta |

---

## 3. Mejoras propuestas

| Mejora | Beneficio | Esfuerzo | Dependencias | Enlaces |
|--------|-----------|----------|--------------|---------|
| **SQLite stub PEI-002** | Supervivencia a reinicio de proceso | Medio | `sqlite3` | `pei-002-tracechain/api/sqlite_store.py` |
| **Documentar TTL por estación** | Operación clara | Bajo | env | [`../../backend/integrations/robotics/README.md`](../../backend/integrations/robotics/README.md) |
| **Extender Pydantic** | Menos datos basura | Bajo | `pydantic` | `neuromorphic_edge.py`, nuevas rutas |
| **Firma en flujo envelope** | Trazabilidad fuerte | Medio | [`../../backend/security/pq_crypto.py`](../../backend/security/pq_crypto.py) | `register_sigpac_digest.py`, stub |
| **Validación en borde** | Parcelas coherentes | Bajo | GDAL / opc. Shapely | `sigpac_validator.py` |
| **GNU Radio** | RF real | Alto | gnuradio | `GNU_RADIO.md` |
| **Fallback Redis → LRU/SQLite** | Resiliencia | Medio | redis, sqlite | `neuromorphic_edge.py` |

---

## 4. Integraciones necesarias

| Integración | Objetivo | Estado | Dependencias | Enlaces |
|-------------|----------|--------|--------------|---------|
| **SNN + SIGPAC** | Riego alineado a uso del suelo | 🟡 Parcial | pei-001, redis | [`../../PLAN-EXCELENCIA-V2.5-REFUERZO.md`](../../PLAN-EXCELENCIA-V2.5-REFUERZO.md) |
| **TraceChain + GaiaChain** | Registro inmutable | ⬜ / 🟡 | `gaia_chain` / servicios | [`../../backend/services/gaia_chain.py`](../../backend/services/gaia_chain.py) |
| **GNU Radio + sensores** | 433 MHz | 📋 Stub | gnuradio | [`../../backend/integrations/robotics/GNU_RADIO.md`](../../backend/integrations/robotics/GNU_RADIO.md) |
| **Nb₂O₅ + SNN** | Latencia física | ⬜ I+D | Hardware | Roadmap memristor |
| **Prometheus + Grafana** | Observabilidad | 🟡 | prometheus_client | [`../monitoring/alerts.md`](../monitoring/alerts.md) |
| **Redis + fallback local** | Resiliencia | ⬜ | sqlite / LRU | `neuromorphic_edge.py` |

---

## 5. Procesos necesarios

| Proceso | Descripción | Estado | Enlaces |
|---------|-------------|--------|---------|
| **Actualización `mapping.json`** | Sincronizar con SIGPAC oficial | ⬜ | [`../../pei-001-sigpac/README.md`](../../pei-001-sigpac/README.md) |
| **Política TTL** | Reglas estación + override numérico | 🟡 (código listo, runbook en README) | `robotics/README.md` |
| **Firma payloads TraceChain** | Dilithium / política DPO | ⬜ | [`../legal/TraceChain-Compliance-2026.md`](../legal/TraceChain-Compliance-2026.md) |
| **Locust** | Carga; **medir** en cada entorno | 🟡 | [`../../tests/stress/README.md`](../../tests/stress/README.md) |
| **DPIA memristores** | Ampliación si aplica | 🟡 | [`../legal/DPIA-Robotics-2026.md`](../legal/DPIA-Robotics-2026.md) |
| **Backup Redis** | RDB/AOF + app | ⬜ | `system_admin_playbook.py` |

---

## 6. Bloque RG (RGPD / cumplimiento)

| Aspecto | Estado | Documentación | Acciones pendientes |
|---------|--------|---------------|---------------------|
| **DPIA SNN / robótica** | 🟡 | [`../legal/DPIA-Robotics-2026.md`](../legal/DPIA-Robotics-2026.md) | Ampliar si el DPO exige memristores / nuevos tratamientos |
| **Minimización en logs** | 🟡 | `system_admin_playbook.py` | Campos estructurados sin datos personales innecesarios |
| **Trazabilidad TraceChain** | 🟡 | [`../legal/TraceChain-Compliance-2026.md`](../legal/TraceChain-Compliance-2026.md) | TX real + firma según despliegue |
| **Licencias GNU Radio** | ⬜ | — | Revisión legal antes de producto comercial con GPL stack |

---

## 7. Correcciones a narrativas obsoletas

| Narrativa obsoleta | Corrección | Evidencia |
|--------------------|------------|-----------|
| “TTL fijo 300 s en `setex`” | TTL **dinámico** + override numérico | `snn_cache_ttl_seconds()` en [`../../backend/integrations/robotics/neuromorphic_edge.py`](../../backend/integrations/robotics/neuromorphic_edge.py) |
| “Nada valida sensores” | La ruta lab usa **`HydroSensorIn`** | `attach_neuromorphic_routes` en el mismo módulo |
| “El sistema para si Redis falla” | **Degradación**: inferencia sin caché | `hydro_infer_dict` + `try/except` en get/setex |
| “Geometrías sin validar” | Validación estructural + **GDAL `IsValid()`** cuando hay osgeo | [`../../backend/integrations/sigpac_validator.py`](../../backend/integrations/sigpac_validator.py) |
| “50 / 350 req/s como datos del repo” | Objetivos o mediciones puntuales **no** son contrato sin archivo de benchmark | Política del checklist: sin SLA sin evidencia |
| “`docs/technical/GNU_RADIO.md`” | Doc viva en **robotics** | [`../../backend/integrations/robotics/GNU_RADIO.md`](../../backend/integrations/robotics/GNU_RADIO.md) |
| “`sign_payload()` en pq_crypto” | API actual: **`dilithium_sign` / `dilithium_verify`** | [`../../backend/security/pq_crypto.py`](../../backend/security/pq_crypto.py) |

---

## 8. Próximos pasos priorizados (P1)

| Acción | Detalle | Enlaces |
|--------|---------|---------|
| **1. Volumen SQLite PEI-002** | Docker/K8s: montar ruta de `PEI002_SQLITE_PATH` | `pei-002-tracechain/api/README.md` |
| **2. Política TTL** | Tabla estación ↔ segundos en README robotics | `backend/integrations/robotics/README.md` |
| **3. Validar TTL** | `pytest tests/integrations/test_neuromorphic_redis_cache.py -k ttl -v` (ajustar `CASTUO_SNN_CACHE_SEASON` vía `monkeypatch` en tests existentes) | `test_neuromorphic_redis_cache.py` |
| **4. Pydantic en nuevas rutas** | No duplicar modelo; extender `HydroSensorIn` si hay nuevos campos | `neuromorphic_edge.py` |
| **5. Firma envelope** | Diseñar campo opcional + verificación en stub o en cliente | `register_sigpac_digest.py`, `pq_crypto.py` |

---

## 9. Comandos `rg` (auditoría técnica)

```bash
rg "setex.*300" backend/integrations/robotics/neuromorphic_edge.py
rg "setex\\(|snn_cache_ttl_seconds" backend/integrations/robotics/neuromorphic_edge.py
rg "HydroSensorIn|neuromorphic_hint_from_metadata" backend/integrations/robotics --glob "*.py"
rg "sigpac_validation_envelopes|parcel_validations|sqlite_store|PEI002_SQLITE" pei-002-tracechain/
rg "digest|dilithium_sign|seal_inference" --glob "*.py"
rg "IsValid\\(|_ring_closed" backend/integrations/sigpac_validator.py
rg "mapping\\.json" --glob "*.py"
rg "gaia_chain|register_event" --glob "*.py"
```

---

*Territorio: el dato mal validado drena confianza como un riego mal calibrado drena el suelo.*
