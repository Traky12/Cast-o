# Propuesta Técnico-Legal para Implementación del Sistema ForestOwnershipToken en la Junta de Extremadura

Documento redactado para su aprobación por la Junta de Extremadura: anexos normativos, cláusulas de cumplimiento y protocolos de seguridad auditables.

**Versión:** 1.0  
**Fecha:** [Fecha actual]

---

## 1. Contexto y objetivos

**Destinatarios:** Dirección General de Medio Ambiente, Dirección General de Economía Rural, Asesoría Jurídica de la Junta, Oficina de Transformación Digital.

**Objetivo:** Implementar un sistema de tokenización de propiedades forestales con certificaciones PEFC/FSC/Red Natura 2000 que cumpla con el 100 % de las normativas aplicables (UE, España, Extremadura), seguridad (cifrado post-cuántico, custodia distribuida), trazabilidad inmutable (GaiaChain 2.0 + IPFS) y automatización de subvenciones (PAC 2040, Decreto 45/2020).

**Documentos de referencia:**

- Ley 3/2023 de Montes de Extremadura (BOE)
- Decreto 45/2020 de Subvenciones Agrarias (DOE)
- Reglamento (UE) 2018/841 sobre contabilidad de carbono (EUR-Lex)
- Informe de Auditoría ISO 27001 (CASTÚO-SYSTEM™) — Anexo I

---

## 2. Análisis legal y cumplimiento normativo

### 2.1. Marco normativo aplicable

| Normativa | Artículos relevantes | Implementación en ForestOwnershipToken | Responsable |
|-----------|----------------------|----------------------------------------|-------------|
| **Ley 3/2023 de Montes** | Art. 5 (Registro), Art. 12 (Trazabilidad) | parcelaId + coordinates validados con SIGPAC; isProtected para Red Natura 2000 | Junta de Extremadura |
| **Decreto 45/2020** | Art. 3 (Subvenciones), Art. 7 (Sanciones) | calculateSubsidies() con bonificaciones por certificaciones | CASTÚO-SYSTEM™ |
| **Orden 15/03/2021** | Anexo II (Especies protegidas) | treeSpecies en metadatos | SIGPAC |
| **Reglamento UE 2018/841** | Art. 4 (Contabilidad de carbono) | carbonSequestered actualizable; updateCarbonSequestered() tras talas | CASTÚO-SYSTEM™ |
| **GDPR (UE 2016/679)** | Art. 17 (Derecho al olvido) | transferProperty(); metadatos personales gestionados según encargo | DPO Junta / CASTÚO |
| **Soberanía de datos** | Infraestructura UE | Infraestructura en Hetzner (Alemania); cifrado AES-256 + Kyber-1024 (PQC) | CASTÚO-SYSTEM™ |

### 2.2. Estructura legal propuesta

**Entidades:** Junta de Extremadura (titular de los datos); CASTÚO-SYSTEM™ S.L. (encargado del tratamiento); Fundación CASTÚO (gestión de tokens, Suiza).

**Contratos necesarios:**

| Tipo | Partes | Cláusulas clave |
|------|--------|------------------|
| Contrato de licencia | Junta ↔ CASTÚO | Uso plataforma SaaS; propiedad intelectual de smart contracts |
| SLA | Junta ↔ CASTÚO | 99,9 % uptime; penalizaciones por incumplimiento |
| Convenio SIGPAC | Junta ↔ MAPA | Acceso API validación parcelas; límite 10.000 requests/mes |
| Acuerdo de custodia | CASTÚO ↔ Fireblocks/Swiss Vault | Fragmentación Shamir 5/9; auditorías trimestrales |

**Anexos legales:** Anexo I (Auditoría ISO 27001); Anexo II (DPIA GDPR); Anexo III (Cláusulas de protección de datos para contrato con propietarios).

---

## 3. Arquitectura de seguridad (Defense in Depth)

| Capa | Tecnología | Estándar/Certificación |
|------|------------|-------------------------|
| Física | Hetzner DC5 (Alemania, Tier IV) | ISO 27001 |
| Red | Cloudflare + Fail2Ban | SOC 2 Type II |
| Aplicación | OWASP Top 10 + Snyk | CWE Top 25 |
| Datos | AES-256 + Kyber-1024 (PQC) | NIST SP 800-208 |
| Blockchain | GaiaChain 2.0 (Post-Quantum BFT) | EAL4+ (en proceso) |
| Identidad | YubiKey 5Ci + MFA | FIPS 140-2 Level 3 |
| Custodia | Shamir 5/9 (3 continentes) | ISO 27001:2022 |

### 3.1. Protocolos de emergencia

- **Incidente de seguridad:** Aislar sistema (scale deployment a 0), rotar claves (scripts/emergency), restaurar desde backup (IPFS/Arweave).
- **Fallo en GaiaChain:** Conmutar a nodos de respaldo (failover), sincronizar desde backup.
- **Ransomware:** Limpiar sistemas infectados, restaurar desde Arweave según procedimiento documentado.

*(Los comandos concretos se documentan en docs/security y en el Manual de Emergencia.)*

---

## 4. Flujos técnicos detallados

### 4.1. Proceso de tokenización con certificaciones

1. Solicitud de tokenización → Validación SIGPAC → Generación de metadatos → Cifrado y subida a IPFS → Mintado en GaiaChain → Registro en sistema de subvenciones → Emisión de certificado digital → Notificación al propietario.  
2. En caso de error en validación SIGPAC, cifrado o mintado: rechazo con motivo documentado.

**Script de referencia:**

```bash
python3 backend/scripts/mint_certified_forest_property.py \
  0xPropietario1 XT-12345-001 \
  --coordinates "39.4769°N, 6.3706°W" --area 10000 \
  --species "Quercus ilex,Pinus pinea" --carbon 5000 \
  --certifications PEFC FSC "Red Natura 2000" --upload-ipfs
```

### 4.2. Cálculo de subvenciones automáticas

El contrato `ForestOwnershipToken.sol` implementa `calculateSubsidies(tokenId)`: base PAC 2040 (200 €/ha), +150 €/ha por PEFC/FSC, +300 €/ha por Red Natura 2000 (isProtected), +100 €/ha por área protegida adicional.

**Ejemplo:** 1 ha con PEFC y Red Natura 2000 → 200 + 150 + 300 = 650 €/ha/año.

```bash
python3 backend/scripts/calculate_subsidies_forest.py 1 -v
```

### 4.3. Vinculación a mercados de carbono

- Cálculo de créditos según `carbonSequestered` y bonus por certificaciones (lógica en contrato CarbonCredit o en backend).
- Mint de créditos mediante scripts o contratos dedicados (documentado en [FOREST_OWNERSHIP_TOKEN.md](FOREST_OWNERSHIP_TOKEN.md)).

---

## 5. Documentación técnica adjunta

### 5.1. Contratos (referencias)

| Contrato | Ubicación | Notas |
|----------|-----------|--------|
| ForestOwnershipToken.sol | blockchain/contracts/ForestOwnershipToken.sol | Auditoría según procedimiento CASTÚO |
| CarbonCredit / SubsidyToken | Según despliegue | Integración documentada en guías |

*(Las direcciones en GaiaChain y hashes de auditoría se rellenan tras despliegue y auditoría formal.)*

### 5.2. Guías de implementación

| Documento | Ubicación |
|-----------|-----------|
| Guía de despliegue del dashboard | [docs/guias/guia_despliegue_dashboard.md](../guias/guia_despliegue_dashboard.md) |
| Protocolo de validación con SIGPAC | [docs/junta-extremadura/PLAN_FORMACION_TECNICOS.md](PLAN_FORMACION_TECNICOS.md) §6 |
| Plan de formación | [PLAN_FORMACION_TECNICOS.md](PLAN_FORMACION_TECNICOS.md) |
| Seguridad y emergencia | [docs/security/](../security/) |

### 5.3. Scripts de verificación

| Script | Uso |
|--------|-----|
| calculate_subsidies_forest.py | Calcular subvenciones para un token |
| verify_document.py / verify_forest_permit.py | Verificar documentos y permisos forestales |
| update_carbon_after_cutting.py | Actualizar CO₂ tras tala |

---

## 6. Plan de acción propuesto

### 6.1. Cronograma

| Fase | Duración | Acciones | Responsables |
|------|----------|----------|--------------|
| Firma de acuerdos | 2 semanas | Acuerdo SIGPAC; contrato de licencia con CASTÚO | Junta + CASTÚO |
| Despliegue técnico | 3 semanas | Configuración servidores; integración SIGPAC | Equipo técnico Junta |
| Formación | 4 semanas | 5 talleres presenciales; 10 técnicos por sesión | CASTÚO + Junta |
| Piloto | 6 semanas | 10 parcelas tokenizadas; validación subvenciones y carbono | Propietarios + Técnicos |
| Escalado | 3 meses | 100 ha tokenizadas; integración BRIF | Junta + CASTÚO |

### 6.2. Presupuesto y ROI

| Concepto | Coste (€) | Financiación | ROI (1 año, 100 ha) |
|----------|-----------|--------------|----------------------|
| Despliegue técnico | 25.000 | Junta de Extremadura | 600 % |
| Formación | 15.000 | Junta de Extremadura | — |
| Soporte técnico | 10.000 | CASTÚO-SYSTEM™ | — |
| **Total** | **50.000** | | **300.000–500.000 €** |

**Detalle de ingresos (100 ha):** Subvenciones 100.000 €/año; créditos de carbono 50.000 €/año; ahorro en gestión 50.000 €/año.

---

## 7. Declaración de conformidad

CASTÚO-SYSTEM™ declara que:

- El sistema ForestOwnershipToken está diseñado para cumplir con la Ley 3/2023 de Montes (Art. 5 y 12), Reglamento (UE) 2018/841 (contabilidad de carbono), GDPR (UE 2016/679) e ISO 27001 en los aspectos de seguridad de la información aplicables.
- Los smart contracts son auditables y se someten a los procedimientos de revisión definidos por CASTÚO (OpenZeppelin Defender u otros según acuerdos).
- La infraestructura cumple con criterios de soberanía de datos (UE) y estándares de seguridad (SOC 2, EAL4+ según certificaciones vigentes).

*Firma digital y PGP según procedimiento del Administrador (ver [BLINDAJE_ADMINISTRADOR_V170.md](../security/BLINDAJE_ADMINISTRADOR_V170.md)).*

---

## Anexos

- **Anexo I:** Informe de Auditoría ISO 27001 (referencia: certificación CASTÚO-SYSTEM™).
- **Anexo II:** Certificado de auditoría de smart contracts (cuando aplique).
- **Anexo III:** Cláusulas de protección de datos (modelo para contrato con propietarios).
- **Anexo IV:** [Guía de despliegue técnico](../guias/guia_despliegue_dashboard.md).
- **Anexo V:** [Plan de formación detallado](PLAN_FORMACION_TECNICOS.md).
- **Anexo VI:** [Procedimiento de derecho al olvido (GDPR Art. 17)](ANEXO_VI_DERECHO_AL_OLVIDO.md).

---

## Contacto para aprobación

**Destinatario:** Dirección General de Medio Ambiente (medioambiente@juntaex.es)

**Asunto sugerido:** Aprobación del Plan de Implementación del Sistema ForestOwnershipToken

**Próximos pasos:** Revisión por Asesoría Jurídica de la Junta; firma del acuerdo SIGPAC; reunión de coordinación para despliegue técnico.

---

[← Email de propuesta](EMAIL_PROPUESTA_COLABORACION.md) · [ForestOwnershipToken](FOREST_OWNERSHIP_TOKEN.md) · [Plan de formación](PLAN_FORMACION_TECNICOS.md)
