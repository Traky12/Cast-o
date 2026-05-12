# Requisitos para una integración futura con CAAE (referencia)

**Revisión:** 2026-03-21 · **Alcance:** planificación; **no** sustituye expediente ni portal del organismo de control.

---

## 1. Marco normativo (consulta oficial)

- **Reglamento (UE) 2018/848** (producción ecológica): texto y actualizaciones en **EUR-Lex**; no se replica aquí como “texto completo en repo”.
- Normativa española de desarrollo y guías: **BOE** y publicaciones del **MAPA** / CCAA; contrastar con asesoramiento.
- **No** citar como vigente una “Orden AAA/XXX/2026” sin **número y fecha oficiales** en BOE.

## 2. Qué hay hoy en el monorepo

- Marco de límites: [CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md](./CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md).
- **No** existe `backend/compliance/caae_integration.py` ni procedimiento generado tipo `compliance_docs/generated/02.04.01_CAAE-Procedimiento.md` en el árbol actual.
- **No** existe plantilla `templates/legal/CAAE-Informe-Trazabilidad.docx` como evidencia versionada (añadir solo si la elaboráis y podéis mantenerla).

## 3. Si en el futuro hubiera canal técnico acordado

Bajo **contrato y documentación oficial** del operador/CAAE (no inferida de briefings):

1. Cliente delgado detrás de interfaz estable (p. ej. `backend/compliance/caae_client.py` — **a crear**).
2. Autenticación, formatos y límites según **especificación entregada por el organismo**, no tablas genéricas inventadas.
3. Trazabilidad de eventos sensibles: alinear con `backend/api/services/gaiachain_service.py` y `POST /api/audit/register-event` (JWT), no con `GaiaChainAuditClient.register_event_in_chain` incrustado en sensores.
4. Tests de integración con entorno de **pruebas** documentado.

## 4. Auditoría de repositorio

El script `scripts/audit/audit_repo_evidence_check.py` **no** implementa `--caae`; valida **presencia de rutas** declaradas en `REQUIRED_EVIDENCE`. Cualquier categoría CAAE específica se añade solo cuando los ficheros existan de verdad.

---

**Relación:** [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md)
