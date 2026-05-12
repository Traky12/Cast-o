# SIGPAC, AEMPS y territorio (marco real del repositorio)

**Impacto territorial:** lo que no está cableado en código no puede sustituir el expediente ante MAPA, FEGA, Junta o AEMPS.

---

## SIGPAC (MAPA / FEGA)

- La **fuente operativa** de parcelas y capas SIGPAC es el ecosistema oficial (visor, servicios cartográficos, procedimientos de la PAC); **no** hay cliente REST autenticado con `SIGPAC_API_KEY` hacia URLs inventadas. **Sí** hay validación **local** de GeoJSON exportado manualmente: `backend/integrations/sigpac_validator.py` (ver [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md)).
- Evidencia documental interna: `compliance_docs/generated/02.05.01_Procedimiento_SIGPAC_Extremadura.md` y criterios de financiación en `docs/funding/PAC2040-Criterios.md`.

## AEMPS (RD 903/2025 y marco de estupefacientes)

- El módulo `compliance/aemps_compliance.py` **estructura solicitudes y listas documentales**; no sustituye el portal ni los trámites oficiales de AEMPS.
- Cualquier “validación de licencia por API pública” debe basarse en **contrato o integración real** acordada con la agencia, no en endpoints ficticios en el código.

## Normativa extremeña citada en documentación CASTUO (p. ej. Ley 3/2023)

- Varios documentos del repo mencionan **Ley 3/2023** en contextos de montes/consentimientos; la titulación y el artículo aplicable deben **confirmarse** con el expediente y asesoramiento jurídico.
- Documento de apoyo en repo: `docs/legal/ANEXO-III-CONFIDENCIALIDAD-Y-PROTECCION-DATOS.md`.

## Trazabilidad técnica en código

- CIS / corcho: `backend/traceability/`.
- Eventos tipo EPCIS en addon: `custom-addons/castu_system/models/epcis_event.py`.

## Junta de Extremadura / “API trazabilidad.juntaex.es”

- **No** existe en el monorepo integración verificada contra ese host; no usar módulos generados por briefing sin contrato y documentación oficial.

## CAAE, PAC ampliada, mercado predictivo, Netafim

- Ver delimitación explícita en [CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md](./CAAE-PAC-MERCADO-MARCO-REPOSITORIO.md).

## IoT (sensores / actuadores / MQTT)

- El código MQTT y agentes vive bajo **`iot/`** y el router **`backend/routers/iot.py`**; no confundir con un `backend/iot/iot_manager.py` inventado en briefings.
- Marco honesto del árbol: [IOT-MARCO-REPOSITORIO.md](../iot/IOT-MARCO-REPOSITORIO.md).

---

**Briefings “SIGPAC avanzado” + clima/ET0 Extremadura:** delimitación frente a código y métricas inventadas → [SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md](./SIGPAC-CLIMA-EXTREMADURA-MARCO-REPOSITORIO.md).

**Relación:** [PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md)
