# Anexo DPIA — Registro de informes SIGPAC y huellas PEI-002 (2026)

**Ámbito:** evaluación de impacto **relativa** a tratamientos que añaden **digest / metadatos** sobre informes PEI-001 y, opcionalmente, **identificadores de parcela** hacia sistemas externos. **No** sustituye al [DPIA-CASTUO-SYSTEM.md](./DPIA-CASTUO-SYSTEM.md) base; lo complementa cuando se active registro automatizado.

**Relación:** [TraceChain-Compliance-2026.md](./TraceChain-Compliance-2026.md) · [RGPD / protocolo](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md)

---

## 1. ¿Hay datos personales?

| Escenario | Riesgo típico | Medida mínima |
|-----------|---------------|---------------|
| Solo **digest** del JSON completo + **conteos** (`cumple`, `porcentaje_cumplimiento`) | Bajo si el informe **no** contiene nombres, NIF, contactos | Minimización en `details` del POST real; no reenviar el fichero completo a terceros sin base legal |
| **`usos_problematicos`** con IDs tipo `CASTUO-001` | Medio si el ID enlaza en otro sistema con **titular real** | Pseudonimización o segregación; acceso por rol; retención acotada |
| **Registro por parcela** con geometría o vínculo a titular | Alto | **No** enviar geometría en payloads externos; DPIA específica + base legal clara |

---

## 1.1. Bases jurídicas (orientativo, no veredicto legal)

- Usos agrícolas y códigos SIGPAC **pueden** no ser datos personales si **no** identifican a una persona física.
- Si `parcela_id` o cruces con catastro/contratos permiten identificar al titular, el tratamiento puede ser **personal** y requiere base legal y DPIA acordes (art. 6 y 35 RGPD) — **lo determina el responsable del tratamiento con asesoramiento jurídico**, no este repositorio.
- Afirmaciones genéricas tipo “interés legítimo por RD 903/2025” o “consentimiento no aplica” **no** sustituyen análisis de caso.

---

## 2. Medidas técnicas (alineables al repo)

- **TLS** en tránsito hacia APIs internas o despliegue Hetzner.
- **Autenticación:** Bearer dedicado al stub de laboratorio (`PEI002_STUB_BEARER_TOKEN`) distinto de cuentas humanas; en producción Castuo, Keycloak + roles `dpo`/`admin` para `/api/audit/register-event`.
- **Cifrado en reposo:** políticas ya descritas para secretos (`pq_crypto`, almacenes); informes en `pei-001-sigpac/reports/` bajo control de acceso del entorno.
- **Trazas:** logs sin volcar geometrías ni datos identificativos innecesarios.

---

## 3. Retención

El plazo de **5 años** u otro solo es válido **tras** análisis legal del expediente (contrato, norma sectorial, obligaciones PAC/cannabis si aplican). Este anexo **no** fija plazo legalmente vinculante.

---

## 4. Derechos ARCO / interesados

Procedimiento alineado al registro de actividades (art. 30 RGPD) y al DPO designado en el ecosistema Castúo. Cualquier export con `parcela_id` debe poder localizarse en inventario de tratamientos.

---

## 5. Stub PEI-002 (`pei-002-tracechain/api/`)

Uso **solo** en laboratorio o red aislada. No procesar datos reales de titulares sin decisión explícita de tratamiento y medidas del cuadro anterior.

---

*Documento orientativo; revisión jurídica previa a producción.*
