# **🌲 CUMPLIMIENTO LEY 3/2023 DE MONTES DE EXTREMADURA (O EQUIVALENTE REGIONAL)**
**Sistema**: CASTÚO-SYSTEM™
**Fecha**: {{ data.generated_at }}
**Versión**: 1.3
**Responsable**: {{ data.dpo.name }} (DPO)

---
## **📌 1. ALCANCE**
Esta documentación demuestra el cumplimiento de CASTÚO-SYSTEM™ con la normativa forestal autonómica/nacional aplicable, en particular con los artículos relacionados con:
- **Gestión sostenible**
- **Consentimientos**
- **Subvenciones**
- **Educación forestal**
- **Conservación de documentos**

---
{% for art_id, article in data.articles.items() %}
## **📌 Artículo {{ art_id }}: {{ article.description }}**

### **📋 Implementación**
{% for item in article.implementation %}
- {{ item }}
{% endfor %}

### **🔍 Evidencias**
{% for evidence in article.evidence %}
- {{ evidence }}
{% endfor %}

---
{% endfor %}

## **📌 2. INTEGRACIÓN CON SIGPAC / SIGIF**
**Estado**: En desarrollo (Hoja de Ruta 2026).
**Objetivo**: Validar automáticamente que las prácticas forestales registradas cumplen con los requisitos del sistema de información geográfica oficial.

**Evidencias Preliminares**:
- Acuerdo con autoridad competente (04.02_Acuerdo_Junta.pdf o equivalente).
- Diagrama de flujo: 01.03_Flujo_Datos_Personales.md.

## **📌 3. PROCEDIMIENTOS ESPECÍFICOS**
### **3.1. Gestión de Consentimientos**
1. **Flujo**: Propietario accede a ConsentManager en el dashboard; selecciona qué datos comparte (ej: carbon_credits, subsidies). Registro en GaiaChain con token_id, timestamp, previous_consents.
2. **Ejemplo de TX**: [0x123...](https://explorer.gaiachain.es/tx/0x123...).

### **3.2. Subvenciones**
**Proceso**: Propietario solicita vía `POST /api/subsidies/claim`. Sistema valida consentimiento y datos catastrales (futura integración SIGPAC/SIGIF). Registro en GaiaChain. **Retención**: 10 años.

**Evidencia**: backend/api/routes/subsidies.py.

---
## **📌 4. CUMPLIMIENTO CON OTROS ARTÍCULOS**
| **Artículo** | **Implementación** | **Evidencia** |
|--------------|--------------------|---------------|
| Gestión sostenible | Backend valida prácticas sostenibles antes de registrar en GaiaChain. | backend/api/services/consent_service.py |
| Educación forestal | Vídeos educativos generados con Stable Diffusion EU (EUPL-1.2). | backend/api/services/media_service.py |
| Conservación | Política de retención en MinIO (OVH). | docker-compose.eu-oss.yml (volúmenes MinIO) |

---
**Firma del Responsable Técnico**:
_________________________
Carlos Martínez
CTO, CASTÚO-SYSTEM™
{{ data.generated_at[:10] }}
