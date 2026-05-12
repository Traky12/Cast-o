# 📜 Prontuario maestro de auditoría interna (Castúo-System) — v2.5

**Objetivo:** comprobar coherencia entre briefings, código y evidencias del repo; eficiencia operativa sin afirmar certificaciones que el git no puede sellar.

**Última verificación:** **84/84** evidencias presentes (ajustar el número si se añaden filas a `REQUIRED_EVIDENCE` en `scripts/audit/audit_repo_evidence_check.py`; incluye plan integración reforzado Castuo 6, diseño integral ecosistema 6, plan excelencia integral, prontuario cifrado/roles v2.5, análisis crítico excelencia v2.5, prontuario consulta crítica y prontuario debilidades/soberanía EU).

---

## 📋 Checklist de evidencias

| ID | Evidencia | Verificada | Notas |
|----|-----------|------------|--------|
| 1.1 | Validación SIGPAC local | ✅ Sí | `sigpac_validator.py` |
| 1.2 | Umbrales climáticos YAML | ✅ Sí | `extremadura_climate.yaml`, `climate_config.py` |
| 1.3 | Informes de auditoría Jinja2 → JSON | ✅ Sí | `audit_generator.py`, `aemps_audit.jinja2` |
| 1.4 | Pruebas SIGPAC + placeholder remoto | ✅ Sí | `test_sigpac_validator.py`, `sigpac_remote_placeholder.py` |
| 1.5 | Pruebas clima + AEMET (mocks) | ✅ Sí | `test_climate_config.py`, `test_aemet_integration.py` |
| 2.1 | Script inventario de auditoría | ✅ Sí | `audit_repo_evidence_check.py` |
| 3.1 | Protocolo auditoría interna legal | ✅ Sí | [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) (v2.4) |
| 4.1 | Marco SIGPAC + clima + informes | ✅ Sí | [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md) |
| 4.2 | `register_event_in_chain` = dict único | ✅ Sí | PROTOCOLO §6.2 |
| 4.3 | Protocolo v2.4 | ✅ Sí | mismo PROTOCOLO |
| 4.4 | Cultivos / umbrales documentados | ✅ Sí | [UMBRALES-CLIMATICOS-EXTREMADURA.md](./UMBRALES-CLIMATICOS-EXTREMADURA.md) |
| 4.5 | Prontuario excelencia (Cursor) | ✅ Sí | [PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md](../PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md) (v2.5) |
| 4.6 | Roadmap integraciones (SIGPAC, GaiaChain, AEMET) | ✅ Sí | [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md) (v2.5) |
| 4.7 | Prontuario debilidades / soberanía EU | ✅ Sí | [PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md](./PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md) |
| 4.8 | Prontuario cifrado y roles v2.5 | ✅ Sí | [PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md](./PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md); inventario `REQUIRED_EVIDENCE` |
| 4.9 | Análisis crítico excelencia v2.5 | ✅ Sí | [ANALISIS-CRITICO-EXCELENCIA-V2.5.md](./ANALISIS-CRITICO-EXCELENCIA-V2.5.md); inventario `REQUIRED_EVIDENCE` |
| 4.10 | Prontuario consulta crítica | ✅ Sí | [PRONTUARIO-MAESTRO-CONSULTA-CRITICA-CASTUO-SYSTEM.md](./PRONTUARIO-MAESTRO-CONSULTA-CRITICA-CASTUO-SYSTEM.md); inventario `REQUIRED_EVIDENCE` |

---

## Criterio de éxito y alcance

Sistema **coherente, eficaz, seguro y auditable**, con inventario **84/84** evidencias y referencias normativas como **documentación**, no como certificación automática.

**Alcance:** `backend/integrations/`, `backend/ctaex/`, `backend/reports/`, `config/`, `docs/legal/`, `scripts/audit/`.

**Metodología:** checklists revisables + `python scripts/audit/audit_repo_evidence_check.py` (inventario de rutas, no análisis estático de AST).

**Normativa (referencia documental):** Reglamento (UE) 2019/1009, RD 903/2025, UNE-EN ISO 19115, UNE 50510, RD 169/2021, Ley 3/2020, UNE-EN ISO 22005; ISO 9001 / UNE 66175 como marco de actuación interna, no certificación por repositorio.

**Ver también:** [PRONTUARIO-MAESTRO-MEJORA-CASTUO-SYSTEM.md](./PRONTUARIO-MAESTRO-MEJORA-CASTUO-SYSTEM.md) (mejora operativa y organizativa; fuera de `REQUIRED_EVIDENCE` hasta ampliar inventario).

**Relación**

- [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md)
- [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md)
- [PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md](./PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md)

---

## 1. Checklist SIGPAC local

| Item | Cumple | Evidencia | Notas |
|------|--------|-----------|--------|
| 1.1 Reproyección 4326→25830 con manejo de errores | Sí | `sigpac_validator._area_ha_with_ogr` | `try/except` + código retorno `Transform` + log |
| 1.2 `IsValid()` tras reproyectar | Sí | mismo módulo | Log error si falla |
| 1.3 Área declarada solo si `properties` + `area_ha` numérica | Sí | `_validate_geojson_impl` | Warning si no numérica |
| 1.4 Registro GaiaChain opcional con fallo logueado | Sí | `_optional_register_chain` | `register_event_in_chain(dict)`; `exc_info=True` |
| 1.5 Estructura Feature + Polygon/MultiPolygon | Sí | `_structural_validate_feature` | Sin asumir solo Polygon |
| 1.6 CRS 25830/32630 sin reproyección; WGS84 por defecto | Sí | `_feature_crs_urn` + rama else | RFC 7946 sin `crs` → 4326 |
| 1.7 Diagnóstico de transformación | Sí | — | **No** `TransformPoint(0,0)`; ver [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md) |
| 1.8 Capa externa `try/except` | Sí | `SIGPACValidator.validate_geojson` | `logger.exception` en errores inesperados |
| 1.9 GDAL opcional (CI / entornos sin osgeo) | Sí | `ImportError` → validación estructural | `requirements-sigpac-gdal.txt` |

---

## 2. Checklist umbrales climáticos

| Item | Cumple | Evidencia | Notas |
|------|--------|-----------|--------|
| 2.1 Validación numérica al cargar YAML | Sí | `ExtremaduraClimateConfig._validate_numeric_thresholds` | Fallo rápido (`ValueError`) si tipos incorrectos |
| 2.2 Fusión `crop_specific` + global | Sí | `_merge_crop_thresholds` + `check_violation` | Cultivos: `cannabis_medicinal`, `tomate_raf`, `vid`, `cereales` |
| 2.3 Umbrales por cultivo en YAML | Sí | `config/extremadura_climate.yaml` | Revisar con asesor agro |
| 2.4 Warnings en evaluación si tipos rotos | Sí | `check_violation` except | Parámetros: `temperature`, `humidity`, `et0` |
| 2.5 Referencias normativas en respuesta | Sí | campo `normative` | No certifican cumplimiento |

**Doc:** [UMBRALES-CLIMATICOS-EXTREMADURA.md](./UMBRALES-CLIMATICOS-EXTREMADURA.md)

---

## 3. Checklist informes Jinja2 → JSON

| Item | Cumple | Evidencia | Notas |
|------|--------|-----------|--------|
| 3.1 `token_id` entero ≥ 1 o str numérico | Sí | `audit_generator._parse_audit_token_id` | Contrato on-chain usa `int` |
| 3.2 Prioridad `token_id` explícito sobre env | Sí | `_optional_report_chain` | Env `CASTUO_AUDIT_REPORT_TOKEN_ID` |
| 3.3 `normative_notice` en raíz JSON | Sí | `aemps_audit.jinja2` + render | Aclara carácter documental |
| 3.4 Escapado seguro | Sí | filtros `\| tojson` | Plantilla línea a línea |
| 3.5 Registro cadena: error logueado | Sí | `register_event_in_chain` + `exc_info=True` | JSON en disco = evidencia primaria si RPC falla |
| 3.6 `sigpac_metadata` nulo | Sí | plantilla | Ramas `if event.sigpac_metadata` |

**Doc:** [INFORMES-AUDITORIA-PERSONALIZADOS.md](./INFORMES-AUDITORIA-PERSONALIZADOS.md)

---

## 4. Checklist documentación (detalle)

| Item | Cumple | Evidencia |
|------|--------|-----------|
| 4.1 Flujo SIGPAC + riesgos | Sí | [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md) |
| 4.2 `register_event_in_chain` = dict único | Sí | [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) §6.2 |
| 4.3 Protocolo v2.4 | Sí | mismo PROTOCOLO |
| 4.4 Cultivos en YAML | Sí | [UMBRALES-CLIMATICOS-EXTREMADURA.md](./UMBRALES-CLIMATICOS-EXTREMADURA.md) |
| 4.5 Prontuario excelencia (Cursor) | Sí | [PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md](../PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md) |
| 4.6 Roadmap integraciones | Sí | [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md) |
| 4.7 Debilidades / soberanía EU | Sí | [PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md](./PRONTUARIO-MAESTRO-DEBILIDADES-POTENCIAL-SOBERANIA-EU.md) |

---

## 5. Checklist auditoría automática (script)

| Item | Cumple | Evidencia |
|------|--------|-----------|
| 5.1–5.5 Presencia de ficheros clave | Sí | `REQUIRED_EVIDENCE` incluye `sigpac_validator.py`, `climate_config.py`, `audit_generator.py`, `aemps_audit.jinja2`, `extremadura_climate.yaml` |
| 5.6 El script **no** parsea AST ni “busca métodos” | Sí | Solo existencia de rutas |

**Corrección:** el hallazgo “no verifica climate_config.py” (ERR-005) era **falso** si el checklist no estaba al día con `REQUIRED_EVIDENCE`.

---

## 6. Resumen de acciones ya integradas (código real)

| ID | Acción | Archivos |
|----|--------|----------|
| ACT-001–003 | Reproyección, `IsValid`, área numérica, logs | `sigpac_validator.py` |
| ACT-004–005 | YAML numérico + `crop_specific` | `climate_config.py`, `extremadura_climate.yaml` |
| ACT-006–007 | `token_id`, `normative_notice` | `audit_generator.py`, `aemps_audit.jinja2` |
| ACT-008–009 | Protocolo + inventario | `PROTOCOLO-…md`, `audit_repo_evidence_check.py` |

---

## 7. Ejecución

```bash
python scripts/audit/audit_repo_evidence_check.py
```

---

**Relación adicional:** [SIGPAC-AEMPS-MARCO-REPOSITORIO.md](./SIGPAC-AEMPS-MARCO-REPOSITORIO.md) · [CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md](./CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md)
