# Plantilla — solicitud de revisión / firma DPO (DPIA Robotics §6)

**Uso:** correo o tarea interna al DPD/DPO. **No** sustituye registro formal si su organización exige herramienta propia. Sustituir corchetes `[...]` antes de enviar.

**Documento de referencia:** [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) (sección 6).

**Coherencia técnica:** [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](./PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) (secretos A/B; sin Opción C en prod).

---

## Asunto (sugerido)

`[Revisión DPD]` DPIA Robotics §6 — registro on-chain opt-in lab (minimización parcela)

---

## Cuerpo

Estimado/a [Nombre DPO],

Solicitamos **revisión y decisión documentada** sobre el **§6** del DPIA orientativo *Robotics 2026* (`docs/legal/DPIA-Robotics-2026.md`), antes de desplegar el **robotics lab stub** en entorno accesible (p. ej. edge/VPS) con **registro en cadena activado**.

**Resumen técnico verificable en código:**

| Punto | Comportamiento por defecto | Revisión DPO si se cambia |
|-------|----------------------------|---------------------------|
| Registro on-chain | Desactivado salvo `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER=1` + RPC/contrato/ABI/clave válidos (§6 DPIA) | Política de claves y contrato |
| Identificador de parcela en `details` | **No** incluido salvo `CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID=1` | Base legal explícita |
| `tokenId` | Entero acordado; cuerpo o `CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID` | Gobierno de datos / taxonomía eventos |
| Fallo de cadena | El endpoint sigue respondiendo; `chain_registration=failed` | Procedimiento de incidencias |

**Adjuntos / enlaces internos:** ruta al Markdown §6 en el repositorio aprobado; evidencia de variables en staging (sin pegar secretos en el correo).

**CC (opcional):** [equipo técnico / responsable tratamiento]

**Respuesta solicitada:** [fecha] — *aprobación con condiciones* / *rechazo motivado* / *requiere reunión*.

Saludos,  
[Nombre] — [Rol] — [Organización]

---

*El agua del piloto no entra en cadena; solo lo que el DPO autorice como dato y finalidad.*
