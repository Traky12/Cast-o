# Documentación final del Acuerdo CTAEX–CASTÚO-SYSTEM
## Estructura completa, enlaces y estado actual

Documento índice para localizar todos los documentos del acuerdo y su estado.

---

## 1. Documentos principales

### 1.1. Acuerdo principal y resúmenes

| Documento | Contenido | Estado | Enlace |
|-----------|-----------|--------|--------|
| **CTAEX-CASTUO-AGREEMENT-SUMMARY.md** | Resumen ejecutivo (licencias, royalties, equity, anexos). | ✅ Actualizado | [docs/CTAEX-CASTUO-AGREEMENT-SUMMARY.md](CTAEX-CASTUO-AGREEMENT-SUMMARY.md) |
| **CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md** | Guía de implementación (checklist, pendientes, recomendaciones, plantillas de email). | ✅ Actualizado | [docs/CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md](CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md) |
| **CTAEX-CASTUO-SIGNING-PRESENTATION-OUTLINE.md** | Esquema para presentación ejecutiva (15–20 diapositivas). | ✅ Actualizado | [docs/CTAEX-CASTUO-SIGNING-PRESENTATION-OUTLINE.md](CTAEX-CASTUO-SIGNING-PRESENTATION-OUTLINE.md) |

### 1.2. Anexos legales (docs/legal/)

| Anexo | Archivo | Contenido principal | Estado | Validación pendiente |
|-------|---------|---------------------|--------|----------------------|
| **I** | [ANEXO-FONDO-I+D-CTAEX-CASTUO.md](legal/ANEXO-FONDO-I+D-CTAEX-CASTUO.md) | Fondo de I+D (10% royalties, Comité Mixto, auditoría). | ✅ Revisado | Firma + auditoría externa. |
| **II** | [ANEXO-II-PROTOCOLO-INTEGRACION-TECNICA.md](legal/ANEXO-II-PROTOCOLO-INTEGRACION-TECNICA.md) | Integración con LIMS/ERP/IoT, APIs, pruebas. | ✅ Revisado | Validar con equipo técnico CTAEX. |
| **III** | [ANEXO-III-CONFIDENCIALIDAD-Y-PROTECCION-DATOS.md](legal/ANEXO-III-CONFIDENCIALIDAD-Y-PROTECCION-DATOS.md) | Confidencialidad (TLS 1.3, AES-256, NDA), PI compartida. | ✅ Revisado | Firma. |
| **IV** | [ANEXO-IV-LISTA-PERSONAL-AUTORIZADO.md](legal/ANEXO-IV-LISTA-PERSONAL-AUTORIZADO.md) | Personal autorizado (3 CTAEX + 3 CASTÚO). | ❌ Pendiente | Sustituir placeholders (ver [Guía sección 4.1](CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md#41-placeholders-en-anexo-iv)). |
| **V** | [ANEXO-V-PROTOCOLO-SEGURIDAD-Y-CUMPLIMIENTO.md](legal/ANEXO-V-PROTOCOLO-SEGURIDAD-Y-CUMPLIMIENTO.md) | Seguridad (GDPR, ISO 27001, RD 903/2025), auditorías. | ✅ Revisado | Validar con equipo de seguridad CTAEX. |
| **VI** | [ANEXO-VI-PLAN-CONTINGENCIA-Y-RECUPERACION.md](legal/ANEXO-VI-PLAN-CONTINGENCIA-Y-RECUPERACION.md) | Contingencia (RTO &lt;4 h, backups, pruebas). | ✅ Revisado | Pruebas con DevOps. |
| **VII** | [ANEXO-VII-METRICAS-EXITO-Y-KPIS.md](legal/ANEXO-VII-METRICAS-EXITO-Y-KPIS.md) | KPIs (financieros, operativos, I+D), informes trimestrales. | ✅ Revisado | Ajustar métricas con CTAEX. |

---

## 2. Estado actual y pendientes

### 2.1. Tabla de pendientes críticos

| Área | Tarea | Responsable | Plazo | Estado |
|------|-------|-------------|-------|--------|
| Anexo IV | Sustituir placeholders con nombres reales (3 CTAEX + 3 CASTÚO). | CTAEX (RRHH) + Gregorio | 3 días | ❌ Pendiente |
| Revisión legal | Abogado revisa Acuerdo Principal + Anexos I–VII. | Legal (ambas partes) | 5 días | ❌ Pendiente |
| Firma | Firma física/digital de todos los documentos. | Ambos | 1 día | ❌ Pendiente |
| Notarización | Opcional: notarizar en Cáceres. | Ambos | 3 días | ❌ Opcional |
| Integración LIMS/ERP | Pruebas con equipo técnico de CTAEX. | Técnico CTAEX | 5 días | ❌ Pendiente |
| Pruebas de contingencia | Ejecutar rollback_to_memory.sh y simular fallos. | DevOps | 10 días | ❌ Pendiente |
| Auditoría de seguridad | Contratar auditor externo (ej.: AENOR). | Seguridad | 7 días | ❌ Pendiente |
| Comité Mixto | Primera reunión para aprobar proyectos I+D. | Comité Mixto | 1 semana | ❌ Pendiente |

### 2.2. Checklist final para lanzamiento

**Documentación**

- [ ] Revisión legal final (Acuerdo Principal + Anexos I–VII).
- [ ] Firma de documentos (física/digital).
- [ ] Notarización (opcional, Cáceres).
- [ ] Sustituir placeholders en Anexo IV (nombres de personal autorizado).

**Implementación técnica**

- [ ] Validar integración con LIMS/ERP (equipo técnico de CTAEX).
- [ ] Pruebas de contingencia (PostgreSQL, GaiaChain, DDoS).
- [ ] Configurar monitorización (Prometheus/Grafana).
- [ ] Auditoría de seguridad inicial (AENOR o similar).

**Operaciones**

- [ ] Primera reunión del Comité Mixto (aprobación de proyectos I+D).
- [ ] Contratar auditor externo para el Fondo I+D.
- [ ] Enviar primer informe trimestral (15 días tras cierre de trimestre).

---

## 3. Plantillas y guías

| Recurso | Ubicación | Uso |
|---------|-----------|-----|
| **Plantilla email — solicitar datos Anexo IV** | [Guía de implementación, sección 6](CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md#6-plantilla-de-email-para-solicitar-datos-del-anexo-iv) | Enviar a RRHH/Legal CTAEX para obtener 3 nombres (LIMS, Calidad, IoT). |
| **Plantilla email — envío documentación final para firma** | [Guía de implementación, § 7](CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md) | Enviar a Legal/CEO CTAEX con todos los documentos adjuntos y próximos pasos. |
| **Recomendaciones finales** (reunión de firma, post-firma, comunicación) | [Guía de implementación, § 8](CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md) | Reunión de firma, archivo, Comité Mixto, comunicación interna/externa. |

---

## 4. Documentos estratégicos

| Documento | Contenido | Uso |
|-----------|-----------|-----|
| **CTAEX-BOLSA-ROADMAP-EXTREMADURA.md** | Contexto de cotización en Extremadura, requisitos BME Growth/Mercado Continuo, impacto del acuerdo CASTÚO en requisitos bursátiles, roadmap 2026–2031, riesgos y conclusión. | Presentaciones a dirección CTAEX, inversores o Junta de Extremadura. |
| **VIABILIDAD-TOTAL-RESUMEN-EJECUTIVO.md** | TRL7 validado, legalidad SL (CASTÚO 360 AGROTECH SL), trazabilidad 5D + GaiaChain/GS1, cumplimiento UE 2026, pitch CTAEX 17/03/2026, JEREMIE 605K€. | Pitch CTAEX, solicitudes JEREMIE y financiación; garantías técnicas y legales. |

---

## 5. Navegación rápida

- **Resumen del acuerdo y enlaces a anexos:** [CTAEX-CASTUO-AGREEMENT-SUMMARY.md](CTAEX-CASTUO-AGREEMENT-SUMMARY.md)
- **Checklist, pendientes, pruebas y plantillas:** [CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md](CTAEX-CASTUO-IMPLEMENTATION-GUIDE.md)
- **Esquema presentación para firma:** [CTAEX-CASTUO-SIGNING-PRESENTATION-OUTLINE.md](CTAEX-CASTUO-SIGNING-PRESENTATION-OUTLINE.md)
- **Roadmap cotización en bolsa (Extremadura):** [CTAEX-BOLSA-ROADMAP-EXTREMADURA.md](CTAEX-BOLSA-ROADMAP-EXTREMADURA.md)
- **Resumen ejecutivo de viabilidad total (TRL7, 5D, JEREMIE):** [VIABILIDAD-TOTAL-RESUMEN-EJECUTIVO.md](VIABILIDAD-TOTAL-RESUMEN-EJECUTIVO.md)
- **Anexos I–VII:** [docs/legal/](legal/)
