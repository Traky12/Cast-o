# DPIA orientativa: robótica y señales (2026)

**Alcance:** evaluación preliminar para uso de módulos `backend/integrations/robotics` y laboratorio WebRTC. **No** sustituye asesoramiento legal ni registro en bases UE de sistemas de IA de alto riesgo cuando aplique.

---

## 1. Categorías de datos posibles

| Origen | Ejemplo | ¿Datos personales? |
|--------|---------|---------------------|
| Sensores de proceso | distancia, IMU, espectro agregado | Normalmente no |
| Logs de evolución | vector de parámetros, digest SHA-256 | No (salvo que se enlace a operador) |
| Voz / vídeo HRI | streaming WebRTC | Sí, salvo anonimización fuerte |
| RF cruda (IQ) | ficheros GNU Radio | Puede revelar ubicación/comportamiento si se conserva |

**Minimización:** el diseño Castúo prioriza **digest + metadatos** hacia cadena/auditoría; no almacenar IQ en backend por defecto.

---

## 2. Bases jurídicas (orientativas)

- **Interés legítimo / ejecución contractual:** telemetría agro-industrial o logística acordada con el responsable.  
- **Consentimiento:** voz, biometría o grabación de personas.  
- **AI Act (UE):** clasificación de riesgo según uso final (médico, crítico, etc.); este repositorio no la determina.

## 3. Medidas técnicas alineadas al código

- Cifrado simétrico de muestras de laboratorio: AES-256-GCM (`signal_manager`).  
- Sellado híbrido / PQC: `pq_crypto.PostQuantumCrypto` vía `RobotSecurityLayer`.  
- Trazabilidad: `register_event_in_chain` con `details` minimizados (`robot_traceability`).  

---

## 4. Riesgos y mitigaciones (resumen)

| Riesgo | Mitigación |
|--------|------------|
| Exfiltración de claves | Vault, rotación, sin claves por defecto en producción |
| Correlación RF ↔ parcela/persona | Política de retención corta para IQ; solo digest en Castúo |
| WebRTC sin control | Autenticación, TURN propio, registro de sesiones |

---

## 5. Retención

Definir por tratamiento; los checkpoints JSON locales no deben contener geometrías ni PII sin base legal específica.

---

## 6. Registro on-chain desde el **robotics lab stub** (opt-in)

Solo si **`CASTUO_ROBOTICS_LAB_CHAIN_REGISTER=1`** y existen **`GAIA_CHAIN_RPC`**, **`GAIA_CHAIN_AUDIT_CONTRACT`**, **`GAIA_CHAIN_AUDIT_ABI`** y **`GAIA_CHAIN_PRIVATE_KEY`** válidos (mismo contrato que `register_event_in_chain` en el monolito).

- **`tokenId`**: entero acordado con gobierno de datos; puede enviarse en el cuerpo (`token_id` / `chain_token_id`) o vía **`CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID`**.
- **Minimización**: por defecto **no** se incluye identificador de parcela en `details` on-chain; solo con **`CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID=1`** (revisión DPO).
- **`neuromorphic_inference`**: si `CASTUO_NEUROMORPHIC_LAB=1` y hay `humedad`/`ph`/`ec` en `metrics_summary`, la respuesta del snapshot puede incluir inferencia + referencia al sellado Dilithium; el payload on-chain solo recoge subcampos acotados (`riego_ml`, `eco_alloy`, `neuro_chain_seal`).

Si la cadena falla, el stub sigue respondiendo con digest y **`chain_registration=failed`** (sin tirar el endpoint).

**Observabilidad:** `GET /health` expone `chain_status` (`disabled` \| `ready` \| `misconfigured`) y si el lab neuromórfico está activo, **sin** Bearer ni secretos.

**Operativa DPO / edge:** plantilla de correo al DPD → [DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md](./DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md). Checklist despliegue TRL6 (Hetzner, secretos, pruebas) → [CHECKLIST-TRL6-HETZNER-STAGING.md](../deploy/CHECKLIST-TRL6-HETZNER-STAGING.md). Evidencia de pruebas verificable (JUnit + manifiesto, sin sustituir DPIA) → [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](./INFORME-EVIDENCIA-TRL6-PLANTILLA.md).

---

*Revisión anual recomendada o ante cambio de hardware/red.*
