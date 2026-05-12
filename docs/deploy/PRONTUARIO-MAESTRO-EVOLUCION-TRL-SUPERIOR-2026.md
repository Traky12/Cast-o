# Prontuario maestro — evolución a TRL superior (2026)

*Hoja de ruta crítica hacia TRL 7–9 con **autoevaluación continua** y gobernanza tipo equipo autónomo/resiliente — siempre con **evidencia medible** del repositorio. Sin afirmar despliegues, certificaciones ni integraciones no demostradas.*

**Relación:** [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) (síntesis componentes + 6 meses) · [PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md](./PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [DIAGNOSTICO-WORKSPACE-CURSOR-2026.md](../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md)

---

## 🗺️ 1. Diagnóstico actual de TRL

*Basado en **evidencia medible** del repositorio; producción prolongada o certificaciones requieren evidencia **fuera** de este archivo.*

| Componente | TRL actual *(rango)* | Evidencia *(verificable en repo)* | Gaps hacia TRL 7–9 *(típicos)* |
|------------|---------------------|-----------------------------------|--------------------------------|
| **SNN** (`neuromorphic_edge.py`) | **4–5** | Tests CI (`pytest -m trl6`); `"trl": "TRL-4-lab-sim"`; staging posible vía [CHECKLIST-TRL6-HETZNER-STAGING](./CHECKLIST-TRL6-HETZNER-STAGING.md) *(si aplica tu entorno)*; **sin** usuarios finales en el propio código | Validación en **campo** (p. ej. 6+ meses) + métricas archivadas |
| **TraceChain** (stub + SQLite) | **5** | Persistencia SQLite (`sqlite_store.py`); smoke volumen 🟡; **sin** nodo GaiaChain en el clon | Integración **GaiaChain real** + auditoría externa |
| **SIGPAC** (`pei-001-sigpac/`) | **6** *(entorno controlado)* | Validación en flujo PEI-001; **sin** despliegue con usuarios finales demostrado solo por el git | Integración con **administraciones** *(si aplica)*; sync `mapping.json` |
| **Señales** (RF / IoT) | **3–4** | [GNU_RADIO.md](../../backend/integrations/robotics/GNU_RADIO.md) stub; `pyserial` en otros paquetes (p. ej. exporters) | Pruebas en entorno real + hardware y normativa espectral |
| **Memristores** (Nb₂O₅ / VO₂) | **2–3** | Roadmap + simulación SNN | Muestras, laboratorio, repetibilidad |
| **Monitorización** | **5** | Histogramas `castuo_neuro_*` opcionales; [alerts.md](../monitoring/alerts.md) | Grafana versionado + **SLO definidos tras línea base** |
| **Seguridad (PQC)** | **5–6** *(🟡)* | Kyber-1024 en [pq_crypto.py](../../backend/security/pq_crypto.py) **si** `pqcrypto`; si no, fallback documentado | Auditoría externa; certificación **si** programa de negocio |
| **Sistema agregado** | **~5–6** *(estimación)* | [DIAGNOSTICO-WORKSPACE-CURSOR-2026.md](../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md) | Campo + cadena + gobernanza + SLO medidos |

**Gaps agregados críticos:** ventana operativa larga con bitácora; integraciones solo con mandato legal/diseño; certificaciones = **programa** externo, no estado del git.

---

## 🔍 2. Autoevaluación interna de TRL

*Criterios basados en **evidencia**, no en métricas inventadas.*

### 2.1. Criterios verificables

| TRL | Criterios *(SNN / TraceChain / plataforma)* | Evidencia requerida *(ejemplos)* |
|-----|---------------------------------------------|----------------------------------|
| **4** | Validación en laboratorio | Código en `neuromorphic_edge.py`, tests en CI |
| **5** | Validación en entorno relevante (staging) | Despliegue documentado; datos representativos; sin usuarios finales o alcance acotado *(p. ej. staging Hetzner: [CHECKLIST-TRL6-HETZNER-STAGING](./CHECKLIST-TRL6-HETZNER-STAGING.md))* |
| **6** | Prototipo en entorno operativo | Uso real acotado + incidencias registradas + métricas básicas *(duración acordada, p. ej. 3+ meses)* |
| **7** | Demostración sostenida en operación | **Ventanas operativas estables** + SLO **medidos** y archivados (uptime, latencia, errores según definición del servicio) |
| **8** | Sistema calificado para un contexto | Certificaciones / auditorías **externas** si el negocio las exige + artefactos |
| **9** | Operación probada en condiciones reales amplias | P. ej. **12+ meses** en producción + SLO cumplidos según acuerdo + gobernanza de cambios |

*Sin fijar porcentajes de uptime globales sin medición y contrato de servicio.*

### 2.2. Autoevaluación actual

| Componente | TRL autoevaluado | Evidencia | Acciones para subir TRL |
|------------|------------------|-----------|-------------------------|
| **SNN** | 4–5 | Tests CI; lab/staging sin usuarios finales en el repo | 1) Producción acotada con usuarios reales. 2) Métricas y ventanas operativas. 3) Validación larga en campo si aplica. |
| **TraceChain** | 5 | SQLite stub funcional; sin nodo GaiaChain en el clon | 1) Integración cadena real. 2) Auditoría externa de trazabilidad. |
| **SIGPAC** | 6 *(controlado)* | `pei-001-sigpac/` + validador; sin usuarios finales acreditados en el repo | 1) Administraciones / registros **si aplica**. 2) Acreditación con informe de tercero si procede. |
| **Señales RF** | 3–4 | Stub GNU Radio | 1) Campo + hardware. 2) Acoplar a SNN en despliegue. |
| **Memristores** | 2–3 | Roadmap, sin prototipo en repo | 1) Muestras. 2) Laboratorio. |
| **Monitorización** | 5 | Prometheus opcional; alertas plantilla | 1) Grafana. 2) SLO tras línea base. |
| **Seguridad (PQC)** | 5–6 🟡 | Kyber-1024 vía `pq_crypto` *(🟡 fallback si no deps)* | 1) Auditoría externa. 2) ISO 27001 u otra **solo** si hay programa formal. |

---

## 🔄 3. Sistema de mejora continua

*Evolución autónoma y resiliente: procesos antes que herramientas concretas.*

### 3.1. Procesos clave

| Proceso | Descripción | Frecuencia | Herramientas / enlace *(ejemplos)* |
|---------|-------------|------------|-----------------------------------|
| **Revisión TRL** | Autoevaluación con artefactos (commits, informes) | Trimestral | [../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md](../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md), este documento |
| **Auditoría de seguridad** | Vulnerabilidades, deps, secretos, uso real de PQC/Kyber | Trimestral | Lockfiles, SCA; *opcional* OpenSCAP, Nessus u homologado corporativo |
| **Pruebas de campo** | SNN / RF cuando haya hardware y permisos | Mensual o por hito | GNU Radio, sensores *(cuando existan)* |
| **Revisión DPIA** | RGPD, AI Act ante cambios | Anual o por cambio de tratamiento | [../legal/DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |
| **Optimización de rendimiento** | TTL, caché, histogramas | Mensual | [../../backend/integrations/robotics/README.md](../../backend/integrations/robotics/README.md), Prometheus, Grafana, Locust |

### 3.2. Roles funcionales *(sin asignación nominal)*

| Rol funcional | Responsabilidades | Herramientas *(sustituibles)* |
|---------------|-------------------|-------------------------------|
| Coordinación técnica | Priorización TRL, riesgos, alineación legal/ops | Issues, ADR, tablero |
| Implementación backend | SNN, TraceChain, APIs, CI | pytest, workflows |
| Integración campo / IoT | RF, sensores | GNU Radio, instrumentación |
| Seguridad y privacidad | Amenazas, PQC, secretos | `pq_crypto`, DPO |
| Observabilidad | Métricas, SLO, postmortems | Prometheus, Grafana, Locust |
| Cumplimiento | DPIA, retención | `docs/legal/` |

---

## 🛡️ 4. Resiliencia y seguridad

*Estrategias **verificables**; no confundir persistencia PEI-002 con caché SNN.*

### 4.1. Resiliencia

| Estrategia | Implementación | Estado | Evidencia |
|------------|----------------|--------|-----------|
| **Inferencia sin Redis** | SNN sigue si Redis cae (sin caché) | 🟡 | [../../backend/integrations/robotics/neuromorphic_edge.py](../../backend/integrations/robotics/neuromorphic_edge.py) |
| **Fallback Redis → SQLite (caché SNN)** | Persistencia de caché si Redis falla *(capa en `neuromorphic_edge` o equivalente)* | ⬜ | Pendiente: implementar en SNN *(no confundir con SQLite PEI-002)* |
| **Persistencia PEI-002** | SQLite stub *(no es fallback de Redis SNN)* | 🟡 | [../../pei-002-tracechain/api/sqlite_store.py](../../pei-002-tracechain/api/sqlite_store.py), [smoke](../../tests/smoke/smoke_test_persistence.sh) |
| **Backup automático** | SQLite / artefactos cadena | ⬜ | Script cron + runbook |
| **Monitorización 24/7** | Alertas fallos críticos | 🟡 | [../monitoring/alerts.md](../monitoring/alerts.md) |
| **Runbook de emergencia** | Recuperación ante desastres | ⬜ | Documentar en playbook ops *(p. ej. `system_admin_playbook.py` o doc dedicado)* |

### 4.2. Seguridad

| Estrategia | Implementación | Estado | Evidencia |
|------------|----------------|--------|-----------|
| **Kyber-1024 / Dilithium** *(🟡)* | Con `pqcrypto`; si no, fallback | 🟡 | [../../backend/security/pq_crypto.py](../../backend/security/pq_crypto.py) |
| **Autenticación (p. ej. YubiKey)** | IdP / servidores críticos | ⬜ | Integración en despliegue producción |
| **Auditorías externas** | Informe tercero | ⬜ | Contrato |
| **RGPD** | Minimización, DPIA | 🟡 | [../legal/DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |
| **Certificaciones (ISO 27001, etc.)** | Programa negocio | ⬜ | No inferible del solo código |

---

## 🤖 5. Equipo autónomo, resiliente y eficaz

### 5.1. Funciones clave *(genéricas)*

| Función | Responsabilidades |
|---------|-------------------|
| **Líder técnico** | Priorización, coordinación entre funciones, revisión TRL |
| **Desarrollador backend** | SNN, TraceChain, rendimiento, tests, CI/CD |
| **Especialista IoT / campo** | GNU Radio, sensores, pruebas de campo, hardware |
| **Experto en seguridad** | Auditorías, cifrado, RGPD / AI Act operativo |
| **Analista de datos** | Métricas, SLO, ajuste de parámetros |
| **Experto legal** | DPIA, PAC, AI Act, registros de tratamiento |

*Sin nombres propios en este documento (política del repositorio). Una persona puede cubrir varias funciones.*

### 5.2. Cultura y procesos

| Principio / proceso | Implementación sugerida | Frecuencia |
|---------------------|-------------------------|------------|
| Autonomía | OKRs o equivalentes por iniciativa | Por trimestre |
| Transparencia | Estado en checklist y ADR | Continuo |
| Mejora continua | Retrospectivas con datos | Trimestral |
| Sincronización | Desbloqueos | Semanal |
| Revisión de métricas | `castuo_neuro_*`, errores | Mensual |
| Gestión de incidentes | Postmortem | Según severidad |

---

## 📈 6. Evolución recomendada hacia TRL 7–9

*Roadmap con **criterios auditables**; plazos orientativos.*

### 6.1. Corto plazo (~3 meses)

| Acción | Objetivo | Plazo orientativo | Criterio de éxito |
|--------|----------|-------------------|-------------------|
| Despliegue en producción | SNN / TraceChain con usuarios reales *(alcance acotado)* | ~1 mes | Bitácora + versión; **ventana** (p. ej. 3+ meses) sin incidentes **críticos** *(definir severidad)* |
| Configurar Grafana | Dashboards `castuo_neuro_*` | ~1 mes | Paneles visibles + al menos una alerta de prueba |
| Firma digital | `dilithium_sign` en flujos acordados | ~1 mes | **Cobertura inventariada y acordada** *(evitar “100 %” sin listado de rutas)* |
| Validar TTL dinámico | Caché por temporada / env | ~1 semana | `rg "setex.*300"` + `pytest -k ttl` |

### 6.2. Medio plazo (~6 meses)

| Acción | Objetivo | Criterio de éxito |
|--------|----------|-------------------|
| Pruebas en campo | SNN / señales RF | Informe: sensores capturados y trazados |
| Integración GaiaChain | Registro inmutable | TX / anclaje demostrable *(alcance acordado)* |
| Optimizar rendimiento | Latencia / throughput | Informe vs **línea base** archivada |
| Integraciones regulatorias | Solo si aplica | Dictamen legal + evidencia técnica *(ej. administraciones — no presuponer AEMPS)* |

### 6.3. Largo plazo (~12 meses)

| Acción | Objetivo | Criterio de éxito |
|--------|----------|-------------------|
| Memristores en laboratorio | I+D Nb₂O₅ / VO₂ | Prototipo + datos repetibles; objetivo de latencia en laboratorio solo si consta en informe |
| Expansión cultivos | Olivar, viñedo, etc. | Informes por cultivo *(número “3+” solo si se define alcance)* |
| Automatización CI/CD | Tests + despliegues | **Tasa de fallo de pipeline** medida y reducida *(no “0 %” sin serie histórica)* |
| Certificaciones | ISO 27001, AI Act, etc. | **Solo** con informe o certificado de tercero |

---

## ⚖️ 7. Cumplimiento legal y ético

### 7.1. RGPD

| Requisito | Acción | Estado | Documentación |
|-----------|--------|--------|---------------|
| Anonimización / minimización | Logs y payloads | 🟡 | [../legal/DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |
| Derechos ARCO | Procedimiento operativo | ⬜ / 🟡 | Documentar con DPO *(p. ej. playbook ops / `system_admin_playbook.py` si centralizáis procedimientos ahí)* |
| Conservación | Retención **a definir con DPO** | ⬜ | DPIA + registro de tratamiento |

### 7.2. AI Act (UE 2024)

| Requisito | Acción | Estado | Documentación |
|-----------|--------|--------|---------------|
| Registro / clasificación | Asesoría si aplica | ⬜ | — |
| Trazabilidad | Logs estructurados | 🟡 | [../../backend/integrations/robotics/README.md](../../backend/integrations/robotics/README.md) |
| Evaluación de riesgos | DPIA | 🟡 | [../legal/DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |

### 7.3. PAC 2040 *(marco)*

| Requisito | Acción | Estado | Documentación |
|-----------|--------|--------|---------------|
| Usos del suelo | `mapping.json` + SIGPAC | 🟡 | [../../pei-001-sigpac/README.md](../../pei-001-sigpac/README.md) |
| Trazabilidad actuaciones | TraceChain + audit | 🟡 | [../legal/TraceChain-Compliance-2026.md](../legal/TraceChain-Compliance-2026.md) |
| Sostenibilidad | KPI hídricos/energéticos en despliegue | ⬜ | [./ROADMAP-MEJORAS-P1-P5-2026.md](./ROADMAP-MEJORAS-P1-P5-2026.md) |

---

## 📊 8. Sistema de autoevaluación continua

### 8.1. Métricas clave

| Métrica | Cómo medir | Frecuencia | Herramienta |
|---------|------------|------------|-------------|
| Uptime / disponibilidad | SLI acordado (ventanas operativas) | Mensual | Prometheus / probes *(si desplegado)* |
| Latencia inferencia SNN | `histogram_quantile` sobre `castuo_neuro_hydro_infer_seconds_bucket` | Semanal | Prometheus |
| Throughput | Locust o gateway sobre p. ej. `POST .../hydroponics/infer` | Diario / por release | Locust, Prometheus *(si expone contadores de API)* |
| Trazabilidad | Ratio eventos vs decisiones *(definir)* | Mensual | Stub + backend |
| Cumplimiento legal | % checklist revisado *(metodología documentada)* | Trimestral | Docs legales + [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) |

### 8.2. Proceso de autoevaluación trimestral

**Revisión de métricas**  
- Analizar Prometheus / Grafana (si existen) frente a **línea base archivada**.  
- Comparar con objetivos cualitativos (p. ej. ventanas operativas estables), no con cifras sin contrato de servicio.

**Evaluación de TRL**  
- Actualizar [../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md](../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md) con enlaces a commits, informes o capturas.  
- Revisar criterios TRL 7–9 (p. ej. meses en producción **demostrados**, no supuestos).

**Identificación de gaps**  
- Listar componentes por debajo del TRL objetivo.  
- Priorizar en [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md).

**Plan de mejora**  
- Issues / tablero del proyecto; plazos sin nombres propios obligatorios.

**Informe de progreso**  
- Stakeholders según gobernanza (p. ej. partners tipo CTAEX — **ejemplo**, no compromiso del repo).  
- Actualizar [ROADMAP-MEJORAS-P1-P5-2026.md](./ROADMAP-MEJORAS-P1-P5-2026.md) si aplica.

---

## 📝 9. Documentación y enlaces críticos

*Desde **`docs/deploy/`**.*

| Documento | Propósito | Estado | Enlace |
|-----------|-----------|--------|--------|
| Prontuario análisis crítico | Debilidades + TRL §10 | ✅ | [./PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md](./PRONTUARIO-MAESTRO-ANALISIS-CRITICO-2026.md) |
| Checklist integraciones | Tareas P1–P3 | ✅ | [./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) |
| Checklist TRL6 staging | Evidencia despliegue | 🟡 | [./CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) |
| Diagnóstico workspace | TRL agregado | 🟡 | [../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md](../DIAGNOSTICO-WORKSPACE-CURSOR-2026.md) |
| **Este documento** | Evolución TRL | ✅ | [./PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md) |
| DPIA Robotics | RGPD | 🟡 | [../legal/DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |
| TraceChain Compliance | Trazabilidad | 🟡 | [../legal/TraceChain-Compliance-2026.md](../legal/TraceChain-Compliance-2026.md) |
| GNU_RADIO.md | RF stub | 📋 | [../../backend/integrations/robotics/GNU_RADIO.md](../../backend/integrations/robotics/GNU_RADIO.md) |
| Roadmap mejoras | P1–P5 | ✅ | [./ROADMAP-MEJORAS-P1-P5-2026.md](./ROADMAP-MEJORAS-P1-P5-2026.md) |
| Prontuario + `rg` | Auditoría técnica | ✅ | [./PRONTUARIO-ANALISIS-CURSOR-INTEGRACIONES-2026.md](./PRONTUARIO-ANALISIS-CURSOR-INTEGRACIONES-2026.md) |
| Alertas | PromQL | 🟡 | [../monitoring/alerts.md](../monitoring/alerts.md) |

---

## 🎯 10. Hoja de ruta TRL 7–9 *(12 meses orientativos)*

### 10.1. Objetivos críticos

| Objetivo | Plazo orientativo | Criterio de éxito *(verificable)* |
|----------|-------------------|-------------------------------------|
| **Hacia TRL 7** operativo | ~6 meses | P. ej. **6+ meses** en producción *documentados* + SLO medidos + incidencias críticas gestionadas *(definir severidad)* |
| Integración **GaiaChain** | ~3 meses | TX / hash vinculados a decisiones **en el alcance acordado** |
| **Memristores** (lab Nb₂O₅) | ~6 meses | Prototipo + informe de laboratorio |
| **Equipo autónomo** | ~3 meses | OKRs o equivalentes + retrospectivas registradas *(sin nombres propios en este repo)* |

### 10.2. Hoja de ruta detallada

| Fase | Acciones | Plazo | Resultados esperados |
|------|----------|-------|----------------------|
| **Mes 1–3** | Despliegue producción acotado; Grafana; firma digital en payloads acordados; validar TTL | ~3 meses | Sistema estable **según bitácora** + métricas iniciales |
| **Mes 4–6** | Pruebas campo SNN/RF; integración GaiaChain; optimizar rendimiento vs baseline | ~3 meses | **Paquete de evidencias** alineado a criterios TRL 7 *(no auto-declaración)* |
| **Mes 7–12** | Memristores lab; expansión cultivos/dominios; CI/CD más fiable; certificaciones **si programa** | ~6 meses | **Avance documentado hacia TRL 8–9** — el nivel final depende de evidencia acumulada, no del calendario del markdown |

---

🚜 *Pa'lante, campeón.* 🌱  

*Autoevaluación continua + funciones autónomas solo tienen sentido si el dato y el TRL beben de la misma fuente que el territorio.*
