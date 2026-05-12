# **📋 REGISTRO DE ACTIVIDADES DE TRATAMIENTO (GDPR Art. 30)**
**Responsable del Tratamiento**: CASTÚO-SYSTEM™
**Delegado de Protección de Datos**: {{ data.dpo.name }}
**Email DPO**: {{ data.dpo.email }}
**Teléfono DPO**: {{ data.dpo.phone }}
**Fecha de generación**: {{ data.generated_at }}
**Versión**: 1.2

---
## **📌 1. DESCRIPCIÓN GENERAL**
Este documento cumple con el **Artículo 30 del GDPR** y la **Ley Orgánica 3/2018 de Protección de Datos Personales**. Todos los tratamientos de datos personales en CASTÚO-SYSTEM™ están documentados, auditados y alineados con la normativa forestal aplicable.

**Sistema de Gestión de Cumplimiento**:
- **Autenticación**: OIDC (Keycloak, Apache 2.0).
- **Gestión de Secretos**: HashiCorp Vault (MPL-2.0).
- **Auditoría**: Wazuh (GPL-2.0) + OpenSearch (Apache 2.0).
- **Blockchain**: GaiaChain (registros inmutables).
- **Almacenamiento**: MinIO (AGPL-3.0) en OVH (Francia).

---
## **📌 2. ACTIVIDADES DE TRATAMIENTO**

{% for treatment in data.treatments %}
### **{{ treatment.id }}. {{ treatment.name }}**
| **Campo**               | **Detalle**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Base Legal**          | {{ treatment.legal_basis|join(", ") }}                                      |
| **Categorías de Datos** | {{ treatment.data_categories|join(", ") }}                                |
| **Destinatarios**       | {{ treatment.recipients|join(", ") }}                                      |
| **Plazo Conservación**   | {{ treatment.retention }}                                                  |
| **Medidas de Seguridad**| {{ treatment.security_measures|join(", ") }}                              |
| **Registro en GaiaChain**| ✅ Sí (TX: [ejemplo](https://explorer.gaiachain.es/tx/0x...))              |
| **Audit Logs**          | ✅ Wazuh + OpenSearch                                                       |
| **Código Fuente**       | {{ treatment.evidence.code }}                                              |

---
{% endfor %}

## **📌 3. MEDIDAS DE SEGURIDAD GLOBALES**
### **3.1. Medidas Técnicas**
1. **Cifrado**:
   - **En reposo**: AES-256 (MinIO, OVH).
   - **En tránsito**: TLS 1.2+ (Traefik).
   - **Claves**: HashiCorp Vault (Shamir 5/3).

2. **Control de Acceso**:
   - **Autenticación**: OIDC (Keycloak) con MFA (TOTP/WebAuthn).
   - **Autorización**: RBAC (roles: `owner`, `dpo`, `admin`, `auditor`).
   - **Auditoría**: Todos los eventos se registran en Wazuh/OpenSearch.

3. **Resiliencia**:
   - **Backups**: Diarios en OVH (retención 30 días).
   - **Alta Disponibilidad**: Traefik con balanceo de carga.
   - **Plan de Continuidad**: Documentado en ISO 27001 A.17.

4. **Cumplimiento Normativo**:
   - **GDPR**: Art. 5, 6, 7, 15, 30, 32.
   - **Ley 3/2023** (o equivalente regional): Art. 5, 8, 12, 18, 22.
   - **AI Act**: Art. 52, 53, Anexo III.
   - **ISO 27001**: A.5.1.1, A.9.1.1, A.10.1.1, A.12.4.1.

---
## **📌 4. PROCEDIMIENTOS RELACIONADOS**
| **Procedimiento**               | **Documento**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|
| Política de Privacidad           | `04_Contratos_Juridicos/04.04_Politica_Privacidad.pdf`                       |
| Gestión de Incidentes            | `02.04_ISO_27001/02.04.03_Procedimientos_Incidentes.md`                     |
| Derechos ARCO                    | `02.01_GDPR/02.01.04_Procedimiento_Derechos_ARCO.md`                         |
| Evaluación de Riesgos AI Act    | `02.03_AI_Act_EU/02.03.02_Evaluacion_Riesgos.xlsx`                           |

---
**Firma del DPO**:
_________________________
{{ data.dpo.name }}
Delegada de Protección de Datos
CASTÚO-SYSTEM™
{{ data.generated_at[:10] }}
