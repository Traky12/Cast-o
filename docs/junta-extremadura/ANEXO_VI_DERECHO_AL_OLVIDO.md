# ANEXO VI: Procedimiento de Derecho al Olvido (GDPR — Art. 17)

Documento técnico-legal para cumplimiento del Reglamento (UE) 2016/679, adaptado al sistema ForestOwnershipToken y alineado con la Ley Orgánica 3/2018 de Protección de Datos (LOPDGDD).

---

## 1. Contexto normativo

### 1.1. Marco legal aplicable

| Normativa | Artículos relevantes | Aplicación en ForestOwnershipToken |
|-----------|----------------------|------------------------------------|
| **GDPR (UE 2016/679)** | Art. 17 (Derecho al olvido) | Procedimiento para borrado de datos personales en metadatos IPFS y actualización en contrato. |
| **LOPDGDD (ES 3/2018)** | Art. 13-15 (Derechos ARCO) | Adaptación del derecho al olvido al marco español. |
| **Ley 3/2023 de Montes** | Art. 8 (Protección de datos) | Excepción: datos catastrales (parcelaId, coordinates) no pueden borrarse por obligación legal. |
| **ISO 27001:2022** | A.18.1.4 (Borrado seguro) | Protocolos de borrado y registro de auditoría. |

**Responsables:**

- **Titular del tratamiento:** Junta de Extremadura (Dirección General de Medio Ambiente).
- **Encargado del tratamiento:** CASTÚO-SYSTEM™ S.L. (CIF: B12345678).
- **DPO:** Delegado de Protección de Datos de la Junta (p. ej. dpo@juntaex.es).

---

## 2. Procedimiento técnico para ejercer el derecho al olvido

### 2.1. Flujo de borrado

1. **Solicitud de borrado** → 2. **Validar identidad** → 3. **Borrar datos personales en metadatos** → 4. **Actualizar contrato en GaiaChain** → 5. **Generar prueba de borrado** → 6. **Notificar al solicitante**.  
2. En caso de error en validación, borrado o actualización: **Rechazar solicitud** con motivo documentado.

### 2.2. Pasos detallados

#### 2.2.1. Solicitud de borrado

- **Formulario oficial (Anexo VI.1):** Datos del solicitante (nombre, DNI, correo), Token ID afectado, motivo (ejercicio derecho al olvido, Art. 17 GDPR).
- **Canales:** Presencial (oficinas Junta Cáceres/Badajoz), online (formulario DPO), correo electrónico a DPO con firma digital.

#### 2.2.2. Validación de identidad

- Verificación documental: DNI/NIE escaneado o certificado digital (FNMT).
- Comprobar en GaiaChain que el solicitante es propietario del token: `ownerOf(tokenId) == address_del_solicitante`.
- Confirmación vía SMS/email (código OTP) según procedimiento de la Junta.

**Script de referencia:** [backend/scripts/verify_identity.py](../../backend/scripts/verify_identity.py).

#### 2.2.3. Borrado de datos personales

- Generar nuevo JSON de metadatos **sin** campos personales (Propietario, DNI, Email); mantener name, description, image, attributes no personales, certifications.
- Subir el nuevo JSON a IPFS y obtener `new_ipfs_hash`.
- Llamar en GaiaChain a `updateMetadata(tokenId, newIpfsHash)` (solo el propietario).

**Scripts:** [erase_personal_data.py](../../backend/scripts/erase_personal_data.py), [execute_right_to_be_forgotten.py](../../backend/scripts/execute_right_to_be_forgotten.py).

#### 2.2.4. Generación de prueba de borrado

- Documento de conformidad (PDF) con: fecha/hora, token ID, hash antiguo y nuevo en IPFS, firma del DPO.
- Salida JSON del script de ejecución (status, token_id, old_ipfs_hash, new_ipfs_hash, timestamp, transaction_hash).

---

## 3. Excepciones y limitaciones

### 3.1. Datos no borrables

| Dato | Motivo legal | Normativa |
|------|--------------|-----------|
| parcelaId | Identificador catastral | Art. 8 Ley 3/2023 de Montes |
| coordinates | Ubicación geográfica | Orden 15/03/2021 |
| certifications | Obligatorias para subvenciones | Decreto 45/2020 |
| carbonSequestered | Contabilidad de carbono | Reglamento UE 2018/841 |

### 3.2. Anonimización cuando no sea posible el borrado

- Sustituir valores personales por `[REDACTED]` en metadatos y volver a subir a IPFS; actualizar contrato con `updateMetadata`.
- Registrar el evento en blockchain con `logRedaction(tokenId, reason)` para trazabilidad (ForestOwnershipToken emite `DataRedacted`).

---

## 4. Registro y auditoría

### 4.1. Log de actividades

Estructura tipo (compatible con ISO 27001):

- request_id, token_id, requester_dni (hash/anonymized), action: `right_to_be_forgotten`, status, old_metadata_hash, new_metadata_hash, timestamp, transaction_hash, redacted_fields.

### 4.2. Auditorías periódicas

| Tipo | Frecuencia | Responsable | Herramienta |
|------|------------|-------------|-------------|
| Revisión de logs | Mensual | DPO Junta | Sistema de logs (Splunk o equivalente) |
| Verificación de borrados | Trimestral | CASTÚO | [audit_redactions.py](../../backend/scripts/audit_redactions.py) |
| Auditoría externa | Anual | Externa (p. ej. Deloitte) | Informe ISO 27001 |

---

## 5. Declaración de conformidad

CASTÚO-SYSTEM™ S.L. declara que el procedimiento descrito está diseñado para cumplir con:

- Art. 17 GDPR (Derecho al olvido).
- Art. 13-15 LOPDGDD (Derechos ARCO).
- ISO 27001:2022 A.18.1.4 (Borrado seguro).
- Ley 3/2023 de Montes de Extremadura Art. 8 (Protección de datos).

*Firma digital según procedimiento del Administrador (PGP); ver [BLINDAJE_ADMINISTRADOR_V170.md](../security/BLINDAJE_ADMINISTRADOR_V170.md).*

---

## Anexos del Anexo VI

| Documento | Descripción |
|----------|-------------|
| Anexo VI.1 | Formulario de solicitud de borrado (PDF editable, gestionado por la Junta). |
| Anexo VI.2 | Script de validación de identidad: [verify_identity.py](../../backend/scripts/verify_identity.py). |
| Anexo VI.3 | Script de ejecución del borrado: [execute_right_to_be_forgotten.py](../../backend/scripts/execute_right_to_be_forgotten.py). |
| Anexo VI.4 | Plantilla de prueba de borrado (PDF para el solicitante, generada por el proceso). |
| Anexo VI.5 | Informe de auditoría de borrados (externo, según acuerdos). |

---

*Este anexo garantiza que el sistema ForestOwnershipToken contempla el derecho al olvido (Art. 17 GDPR) con procedimiento claro, borrado selectivo de datos personales (manteniendo datos catastrales obligatorios) y pruebas de auditoría para demostrar conformidad.*

---

[← Propuesta técnico-legal](PROPUESTA_TECNICO_LEGAL_FORESTOWNERSHIPTOKEN.md) · [ForestOwnershipToken](FOREST_OWNERSHIP_TOKEN.md)
